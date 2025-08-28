#!/usr/bin/env python3
"""
Database Schema Management System for CompliantGuard
Handles DDL/DML migrations across environments with versioning
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError


class DatabaseSchemaManager:
    def __init__(self, environment: str = "local"):
        self.environment = environment
        self.dynamodb = boto3.resource("dynamodb", region_name=self.get_region())
        self.schema_version_table = "themisguard-schema-versions"
        self.migrations_dir = "scripts/migrations"
        
    def get_region(self) -> str:
        """Get AWS region based on environment"""
        regions = {
            "local": "us-east-1",
            "staging": "us-east-1", 
            "production": "us-east-1"
        }
        return regions.get(self.environment, "us-east-1")
    
    def ensure_schema_version_table(self):
        """Create schema version tracking table if it doesn't exist"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.schema_version_table,
                KeySchema=[
                    {"AttributeName": "migration_id", "KeyType": "HASH"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "migration_id", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            table.wait_until_exists()
            print(f"✅ Created schema version table: {self.schema_version_table}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceInUseException":
                raise
            print(f"📋 Schema version table already exists: {self.schema_version_table}")
    
    def get_applied_migrations(self) -> set:
        """Get list of migrations that have been applied"""
        try:
            table = self.dynamodb.Table(self.schema_version_table)
            response = table.scan()
            return {item["migration_id"] for item in response["Items"]}
        except ClientError:
            print("⚠️ Could not read applied migrations, assuming none applied")
            return set()
    
    def record_migration(self, migration_id: str, migration_data: Dict):
        """Record that a migration has been applied"""
        try:
            table = self.dynamodb.Table(self.schema_version_table)
            table.put_item(
                Item={
                    "migration_id": migration_id,
                    "applied_at": datetime.utcnow().isoformat(),
                    "environment": self.environment,
                    "migration_data": migration_data
                }
            )
            print(f"📝 Recorded migration: {migration_id}")
        except ClientError as e:
            print(f"❌ Failed to record migration {migration_id}: {e}")
            raise
    
    def load_migrations(self) -> List[Dict]:
        """Load migration files from migrations directory"""
        migrations = []
        migrations_path = os.path.join(os.path.dirname(__file__), "..", self.migrations_dir)
        
        if not os.path.exists(migrations_path):
            print(f"⚠️ Migrations directory does not exist: {migrations_path}")
            return migrations
            
        for filename in sorted(os.listdir(migrations_path)):
            if filename.endswith('.json'):
                filepath = os.path.join(migrations_path, filename)
                try:
                    with open(filepath, 'r') as f:
                        migration = json.load(f)
                        migration['filename'] = filename
                        migration['migration_id'] = filename.replace('.json', '')
                        migrations.append(migration)
                except Exception as e:
                    print(f"❌ Failed to load migration {filename}: {e}")
                    
        return migrations
    
    def apply_table_migration(self, migration: Dict) -> bool:
        """Apply a DynamoDB table migration"""
        try:
            if migration['action'] == 'create_table':
                table_name = migration['table_name']
                
                # Check if table already exists
                try:
                    existing_table = self.dynamodb.Table(table_name)
                    existing_table.load()
                    print(f"📋 Table already exists: {table_name}")
                    return True
                except ClientError:
                    pass  # Table doesn't exist, proceed with creation
                
                # Create table
                create_params = {
                    'TableName': table_name,
                    'KeySchema': migration['key_schema'],
                    'AttributeDefinitions': migration['attribute_definitions'],
                    'BillingMode': migration.get('billing_mode', 'PAY_PER_REQUEST')
                }
                
                if 'global_secondary_indexes' in migration:
                    create_params['GlobalSecondaryIndexes'] = migration['global_secondary_indexes']
                
                table = self.dynamodb.create_table(**create_params)
                table.wait_until_exists()
                print(f"✅ Created table: {table_name}")
                
            elif migration['action'] == 'update_table':
                # Handle table updates (add GSI, modify throughput, etc.)
                table_name = migration['table_name']
                table = self.dynamodb.Table(table_name)
                
                if 'add_gsi' in migration:
                    # Add Global Secondary Index
                    table.update(
                        GlobalSecondaryIndexUpdates=[
                            {
                                'Create': migration['add_gsi']
                            }
                        ]
                    )
                    print(f"✅ Added GSI to table: {table_name}")
                    
            elif migration['action'] == 'delete_table':
                # Handle table deletion (use with extreme caution!)
                table_name = migration['table_name']
                if migration.get('confirm_delete') == True:
                    table = self.dynamodb.Table(table_name)
                    table.delete()
                    print(f"🗑️ Deleted table: {table_name}")
                else:
                    print(f"⚠️ Skipping table deletion (confirm_delete not set): {table_name}")
                    
            return True
            
        except ClientError as e:
            print(f"❌ Failed to apply table migration: {e}")
            return False
    
    def apply_data_migration(self, migration: Dict) -> bool:
        """Apply a data migration (DML operations)"""
        try:
            table_name = migration['table_name']
            table = self.dynamodb.Table(table_name)
            
            if migration['action'] == 'insert_items':
                # Batch insert items
                with table.batch_writer() as batch:
                    for item in migration['items']:
                        batch.put_item(Item=item)
                print(f"✅ Inserted {len(migration['items'])} items into {table_name}")
                
            elif migration['action'] == 'update_items':
                # Update existing items
                for update in migration['updates']:
                    table.update_item(**update)
                print(f"✅ Updated {len(migration['updates'])} items in {table_name}")
                
            elif migration['action'] == 'delete_items':
                # Delete items
                with table.batch_writer() as batch:
                    for key in migration['keys']:
                        batch.delete_item(Key=key)
                print(f"🗑️ Deleted {len(migration['keys'])} items from {table_name}")
                
            return True
            
        except ClientError as e:
            print(f"❌ Failed to apply data migration: {e}")
            return False
    
    def run_migrations(self) -> bool:
        """Run all pending migrations"""
        print(f"🚀 Starting migration run for environment: {self.environment}")
        
        # Ensure schema version table exists
        self.ensure_schema_version_table()
        
        # Load migrations
        migrations = self.load_migrations()
        if not migrations:
            print("📝 No migrations found")
            return True
            
        # Get applied migrations
        applied = self.get_applied_migrations()
        
        # Apply pending migrations
        success_count = 0
        for migration in migrations:
            migration_id = migration['migration_id']
            
            if migration_id in applied:
                print(f"⏭️ Skipping already applied migration: {migration_id}")
                continue
                
            print(f"🔄 Applying migration: {migration_id}")
            print(f"   Description: {migration.get('description', 'No description')}")
            
            success = False
            if migration['type'] == 'table':
                success = self.apply_table_migration(migration)
            elif migration['type'] == 'data':
                success = self.apply_data_migration(migration)
            else:
                print(f"❌ Unknown migration type: {migration['type']}")
                continue
                
            if success:
                self.record_migration(migration_id, migration)
                success_count += 1
                print(f"✅ Migration applied successfully: {migration_id}")
            else:
                print(f"❌ Migration failed: {migration_id}")
                return False
        
        print(f"🎉 Migration run complete! Applied {success_count} new migrations")
        return True
    
    def list_migrations(self):
        """List all migrations and their status"""
        migrations = self.load_migrations()
        applied = self.get_applied_migrations()
        
        print(f"📋 Migration Status for {self.environment}:")
        print("-" * 70)
        
        for migration in migrations:
            migration_id = migration['migration_id']
            status = "✅ APPLIED" if migration_id in applied else "⏳ PENDING"
            print(f"{status} | {migration_id} | {migration.get('description', '')}")
            
        print(f"\nTotal: {len(migrations)} migrations, {len(applied)} applied")


def main():
    if len(sys.argv) < 2:
        print("Usage: python database-schema-manager.py <command> [environment]")
        print("Commands: migrate, list, status")
        print("Environments: local, staging, production")
        sys.exit(1)
        
    command = sys.argv[1]
    environment = sys.argv[2] if len(sys.argv) > 2 else "local"
    
    manager = DatabaseSchemaManager(environment)
    
    if command == "migrate":
        success = manager.run_migrations()
        sys.exit(0 if success else 1)
    elif command == "list":
        manager.list_migrations()
    elif command == "status":
        manager.list_migrations()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
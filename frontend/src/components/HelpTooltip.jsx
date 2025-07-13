import React, { useState } from 'react';
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline';

const HelpTooltip = ({ content, title, placement = 'top' }) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        type="button"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        className="text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600"
      >
        <QuestionMarkCircleIcon className="h-4 w-4" />
      </button>
      
      {isVisible && (
        <div
          className={`
            absolute z-10 w-80 px-3 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg shadow-sm
            ${placement === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'}
            ${placement === 'left' ? 'right-0' : 'left-0'}
          `}
        >
          {title && (
            <div className="font-semibold mb-1">{title}</div>
          )}
          <div className="text-gray-300">{content}</div>
          
          {/* Arrow */}
          <div
            className={`
              absolute w-2 h-2 bg-gray-900 transform rotate-45
              ${placement === 'top' ? 'top-full -mt-1' : 'bottom-full -mb-1'}
              left-4
            `}
          />
        </div>
      )}
    </div>
  );
};

export default HelpTooltip;
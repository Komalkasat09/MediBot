import React from 'react';

const Loader = () => {
  return (
    <div className="flex items-center space-x-2">
      <div className="w-2 h-2 rounded-full animate-pulse bg-cyan-400"></div>
      <div className="w-2 h-2 rounded-full animate-pulse bg-cyan-400" style={{ animationDelay: '0.2s' }}></div>
      <div className="w-2 h-2 rounded-full animate-pulse bg-cyan-400" style={{ animationDelay: '0.4s' }}></div>
    </div>
  );
};

export default Loader;
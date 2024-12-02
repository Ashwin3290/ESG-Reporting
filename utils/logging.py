import functools
import logging
import os
import traceback
from datetime import datetime
from typing import Any, Callable

class KPILogger:
    def __init__(self):
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Set up logging configuration
        self.logger = logging.getLogger('KPILogger')
        self.logger.setLevel(logging.DEBUG)
        
        # Create file handler with timestamp in filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f'logs/kpi_processing_{timestamp}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log_execution(self, func: Callable) -> Callable:
        """
        Decorator to log function execution details
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            class_name = args[0].__class__.__name__ if args else ''
            func_name = func.__name__
            
            # Log function entry
            self.logger.info(f"{'='*50}")
            self.logger.info(f"Entering {class_name}.{func_name}")
            
            # Log arguments if any
            if len(args) > 1 or kwargs:
                self.logger.debug(f"Arguments: {args[1:] if len(args) > 1 else ''}")
                self.logger.debug(f"Keyword arguments: {kwargs if kwargs else ''}")
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log successful execution
                self.logger.info(f"Successfully executed {class_name}.{func_name}")
                if result is not None:
                    self.logger.debug(f"Return value: {result}")
                
                return result
                
            except Exception as e:
                # Log error details
                self.logger.error(f"Error in {class_name}.{func_name}: {str(e)}")
                self.logger.error(f"Traceback:\n{traceback.format_exc()}")
                raise
            
            finally:
                self.logger.info(f"Exiting {class_name}.{func_name}")
                self.logger.info(f"{'='*50}\n")
        
        return wrapper

# Initialize logger
kpi_logger = KPILogger()

# Decorator for logging DataFrame operations
def log_dataframe_info(func: Callable) -> Callable:
    """
    Decorator specifically for logging DataFrame-related operations
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('KPILogger')
        
        try:
            # Log pre-execution DataFrame state
            if len(args) > 1 and hasattr(args[1], 'shape'):
                df = args[1]
                logger.debug(f"Input DataFrame shape: {df.shape}")
                logger.debug(f"Input DataFrame columns: {df.columns.tolist()}")
                logger.debug(f"Input DataFrame head:\n{df.head()}")
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Log post-execution DataFrame state if result is a DataFrame
            if hasattr(result, 'shape'):
                logger.debug(f"Output DataFrame shape: {result.shape}")
                logger.debug(f"Output DataFrame columns: {result.columns.tolist()}")
                logger.debug(f"Output DataFrame head:\n{result.head()}")
            
            return result
            
        except Exception as e:
            logger.error(f"DataFrame operation error: {str(e)}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
    
    return wrapper
LOGGING_CONFIG = { 
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': { 
        'standard': { 
            'format': '%(asctime)s [%(levelname)s] <%(name)s>: %(message)s'
        },
        'verbose': { 
            'format': '%(asctime)s [%(levelname)s] <%(name)s>: %(message)s'
        },
    },
    'handlers': { 
        'default': { 
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
        'file': { 
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'mode': 'a',  # Append mode
            'maxBytes': 10485760, 
            'backupCount': 5,     
        },
    },
    'loggers': { 
        '': {  # root logger
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'app': { 
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        '__main__': { 
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        },
    } 
}
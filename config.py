# Server Specific Configurations
server = {
    'port': '8081',
    'host': '127.0.0.1'
}

# Pecan Application Configurations
app = {
    'root': 'st2installer.controllers.root.RootController',
    'modules': ['st2installer'],
    'static_root': '%(confdir)s/public',
    'template_path': '%(confdir)s/st2installer/templates',
    'debug': True,
    'errors': {
        404: '/error/404',
        '__force_dict__': True
    }
}

logging = {
    'root': {'level': 'INFO', 'handlers': ['console']},
    'loggers': {
        'st2installer': {'level': 'DEBUG', 'handlers': ['console', 'logfile']},
        'pecan': {'level': 'DEBUG', 'handlers': ['console', 'logfile']},
        'py.warnings': {'handlers': ['console', 'logfile']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color'
        },
	'logfile': {
	    'level': 'DEBUG',
	    'class': 'logging.FileHandler',
	    'filename': 'access.log',
	    'formatter': 'messageonly'
	}
    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        },
	'messageonly': {
	    'format': '%(message)s'
	},
        'color': {
            '()': 'pecan.log.ColorFormatter',
            'format': ('%(asctime)s [%(padded_color_levelname)s] [%(name)s]'
                       '[%(threadName)s] %(message)s'),
        '__force_dict__': True
        }
    }
}

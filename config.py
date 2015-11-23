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
    },
    'version': '0.1.0'
}

logging = {
    'root': {'level': 'INFO', 'handlers': ['console']},
    'loggers': {
        'st2installer': {'level': 'DEBUG', 'handlers': ['console']},
        'pecan': {'level': 'DEBUG', 'handlers': ['console']},
        'py.warnings': {'handlers': ['console']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color'
        },
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

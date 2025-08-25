# Nautobot Advanced Configuration Settings

*This document provides detailed configuration options for advanced Nautobot customization. For basic setup, see the main README.md file.*

## 🔧 Advanced Configuration Options

### Database Configuration

#### PostgreSQL Settings

```python
# config/nautobot_config.py

DATABASES = {
    'default': {
        'NAME': os.getenv('POSTGRES_DB', 'nautobot'),
        'USER': os.getenv('POSTGRES_USER', 'nautobot'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'nautobotpassword'),
        'HOST': os.getenv('NAUTOBOT_DB_HOST', 'postgres'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'disable',
        },
    }
}
```

#### Redis Configuration

```python
# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.getenv('NAUTOBOT_REDIS_HOST', 'redis')}:6379/0",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### Plugin Configuration

#### Device Onboarding Plugin

```python
# Device Onboarding settings
PLUGINS_CONFIG = {
    'nautobot_device_onboarding': {
        'default_site': 'Main',
        'default_device_role': 'Switch',
        'default_device_status': 'Active',
        'platform_map': {
            'cisco_ios': 'Cisco IOS',
            'cisco_nxos': 'Cisco NX-OS',
            'arista_eos': 'Arista EOS',
            'juniper_junos': 'Juniper JUNOS',
        },
        'object_count_strategy': 'exact',
        'create_management_interface': True,
        'management_prefix_length': 24,
    }
}
```

#### Golden Config Plugin

```python
# Golden Config settings
PLUGINS_CONFIG = {
    'nautobot_golden_config': {
        'enable_backup': True,
        'enable_compliance': True,
        'enable_intended': True,
        'enable_sotagg': True,
        'sot_agg_transposer': None,
        'enable_postprocessing': False,
        'postprocessing_callables': [],
        'postprocessing_subscribed_tasks': [],
        'jinja_env': {
            'trim_blocks': True,
            'lstrip_blocks': True,
        },
        'default_settings': {
            'backup_path_template': '{{obj.site.slug}}/{{obj.name}}.cfg',
            'intended_path_template': '{{obj.site.slug}}/{{obj.name}}.cfg',
            'jinja_path_template': '{{obj.platform.slug}}/{{obj.platform.slug }}_main.j2',
            'backup_test_connectivity': False,
        },
    }
}
```

### Security Configuration

#### Authentication Settings

```python
# Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'nautobot.core.authentication.ObjectPermissionBackend',
]

# Session security
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

#### HTTPS Configuration

```python
# HTTPS settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Performance Configuration

#### Celery Settings

```python
# Celery configuration
CELERY_BROKER_URL = f"redis://{os.getenv('NAUTOBOT_REDIS_HOST', 'redis')}:6379/0"
CELERY_RESULT_BACKEND = f"redis://{os.getenv('NAUTOBOT_REDIS_HOST', 'redis')}:6379/0"
CELERY_TASK_SOFT_TIME_LIMIT = 300
CELERY_TASK_TIME_LIMIT = 600
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'nautobot_golden_config.backup_job': {
        'task': 'nautobot_golden_config.tasks.backup_configurations',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
    'nautobot_golden_config.intended_job': {
        'task': 'nautobot_golden_config.tasks.generate_intended_configurations',
        'schedule': crontab(minute=0, hour='*/12'),  # Every 12 hours
    },
    'nautobot_golden_config.compliance_job': {
        'task': 'nautobot_golden_config.tasks.generate_compliance_report',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
    },
}
```

#### Database Optimization

```python
# Database optimization
DATABASES = {
    'default': {
        # ... existing settings ...
        'OPTIONS': {
            'sslmode': 'disable',
            'connect_timeout': 10,
            'application_name': 'nautobot',
        },
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Query optimization
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
        },
    }
```

### Logging Configuration

#### Comprehensive Logging Setup

```python
# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/opt/nautobot/logs/nautobot.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'nautobot': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'nautobot_golden_config': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### API Configuration

#### REST API Settings

```python
# REST API configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'nautobot.core.api.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'nautobot.core.api.renderers.FormlessBrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'nautobot.core.api.pagination.OptionalLimitOffsetPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
    'DEFAULT_VERSION': '1.0',
    'ALLOWED_VERSIONS': ['1.0'],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}
```

#### GraphQL Configuration

```python
# GraphQL configuration
GRAPHENE = {
    'SCHEMA': 'nautobot.core.graphql.schema.Query',
    'MIDDLEWARE': [
        'nautobot.core.graphql.middleware.AuthenticationMiddleware',
        'nautobot.core.graphql.middleware.PermissionMiddleware',
    ],
}
```

### Customization Options

#### Custom Fields

```python
# Custom fields configuration
CUSTOM_FIELD_MODELS = [
    'dcim.device',
    'dcim.interface',
    'ipam.ipaddress',
    'tenancy.tenant',
]

# Custom field types
CUSTOM_FIELD_TYPES = {
    'text': 'nautobot.core.forms.CustomFieldTextForm',
    'longtext': 'nautobot.core.forms.CustomFieldLongTextForm',
    'integer': 'nautobot.core.forms.CustomFieldIntegerForm',
    'boolean': 'nautobot.core.forms.CustomFieldBooleanForm',
    'date': 'nautobot.core.forms.CustomFieldDateForm',
    'url': 'nautobot.core.forms.CustomFieldURLForm',
    'json': 'nautobot.core.forms.CustomFieldJSONForm',
    'select': 'nautobot.core.forms.CustomFieldSelectForm',
    'multiselect': 'nautobot.core.forms.CustomFieldMultiSelectForm',
}
```

#### Custom Validators

```python
# Custom validators
CUSTOM_VALIDATORS = {
    'dcim.device': {
        'name': ['nautobot.core.validators.CustomValidator'],
    },
    'dcim.interface': {
        'name': ['nautobot.core.validators.CustomValidator'],
    },
}
```

### Environment-Specific Settings

#### Development Settings

```python
# Development-specific settings
if os.getenv('ENVIRONMENT', 'production') == 'development':
    DEBUG = True
    ALLOWED_HOSTS = ['*']
    
    # Development logging
    LOGGING['loggers']['django.db.backends'] = {
        'handlers': ['console'],
        'level': 'DEBUG',
    }
    
    # Development cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
```

#### Production Settings

```python
# Production-specific settings
if os.getenv('ENVIRONMENT', 'production') == 'production':
    DEBUG = False
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    
    # Production security
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Production cache
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': f"redis://{os.getenv('NAUTOBOT_REDIS_HOST', 'redis')}:6379/0",
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                },
            }
        }
    }
```

## 🔄 Applying Configuration Changes

After modifying the configuration:

1. **Restart Nautobot**:
   ```bash
   docker-compose restart nautobot
   ```

2. **Check logs** for any errors:
   ```bash
   docker-compose logs nautobot
   ```

3. **Verify configuration**:
   ```bash
   docker-compose exec nautobot nautobot-server check
   ```

4. **Apply migrations** (if needed):
   ```bash
   docker-compose exec nautobot nautobot-server migrate
   ```

## 📚 Additional Resources

- [Nautobot Configuration Documentation](https://docs.nautobot.com/projects/core/en/stable/configuration/)
- [Plugin Configuration Guide](https://docs.nautobot.com/projects/core/en/stable/plugins/configuration/)
- [Security Best Practices](https://docs.nautobot.com/projects/core/en/stable/security/)
- [Performance Tuning](https://docs.nautobot.com/projects/core/en/stable/installation/performance/)

---

*For basic setup and usage, refer to the main README.md file.*

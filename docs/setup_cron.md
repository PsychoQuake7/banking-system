# Cron Job Setup Guide

The Kayamanan Banking System uses `django-crontab` to manage periodic tasks like interest accrual.

## Prerequisites

Ensure `django-crontab` is installed:
```bash
pip install django-crontab
```

## Configuration

Cron jobs are defined in `kayamanan/settings.py` under the `CRONJOBS` setting:

```python
CRONJOBS = [
    # Daily interest computation at 11:59 PM
    ('59 23 * * *', 'django.core.management.call_command', ['compute_interest']),
    # Monthly interest capitalization on the 1st of each month at midnight
    ('0 0 1 * *', 'django.core.management.call_command', ['compute_interest', '--capitalize']),
]
```

## Managing Cron Jobs

### Add Cron Jobs
To add the defined cron jobs to the system's crontab:
```bash
python manage.py crontab add
```

### Remove Cron Jobs
To remove all cron jobs associated with this project:
```bash
python manage.py crontab remove
```

### Show Current Jobs
To list the currently active cron jobs for this project:
```bash
python manage.py crontab show
```

## Troubleshooting

- **Permissions**: Ensure the user running the cron job has write access to the log files and database.
- **Environment**: Cron jobs run in a limited environment. If you encounter "command not found" errors, ensure absolute paths are used or environment variables are set correctly in the cron definition.
- **Logs**: Check system cron logs (usually `/var/log/cron` or `/var/log/syslog`) for execution errors.

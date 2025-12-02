# Notifications & Alerts System

## Overview
The Kayamanan Banking System includes a comprehensive notification and alert system that sends SMS/Email reminders and alerts to users and administrators.

## Features

### 1. SMS/Email Reminders for Payments ✅
- **Location**: `notifications/management/commands/send_due_date_reminders.py`
- **Functionality**: Sends payment reminders to borrowers via email and SMS
- **Schedule**: Should be run daily via cron job
- **Details**:
  - Sends reminders for payments due within the next 7 days
  - Includes payment amount, due date, and days remaining
  - Sent via both email and SMS (SMS is currently mocked/logged)

**Usage**:
```bash
python manage.py send_due_date_reminders
```

**Cron Setup** (add to crontab):
```bash
0 9 * * * cd /path/to/banking-system && python manage.py send_due_date_reminders
```

### 2. Notifications for Loan Approvals ✅
- **Location**: `loans/views.py` - `approve_loan_application_view()`
- **Functionality**: Automatically sends notification when a loan is approved
- **Details**:
  - Sent to borrower when loan application is approved
  - Includes loan amount and application ID
  - Notification type: `loan_approved`

**Trigger**: Automatic when staff approves a loan application

### 3. Notifications for Due Dates ✅
- **Location**: `notifications/management/commands/send_due_date_reminders.py`
- **Functionality**: Sends reminders for upcoming payment due dates
- **Details**:
  - Sends reminders 7 days before due date
  - Daily reminders within the final week
  - Includes days remaining until due date

**Usage**: Same as payment reminders (see #1)

### 4. Admin Alerts for Overdue Loans ✅
- **Location**: `notifications/management/commands/send_admin_overdue_alerts.py`
- **Functionality**: Sends alerts to all admin users about overdue loans
- **Details**:
  - Summarizes total delinquent accounts
  - Shows total overdue amount
  - Categorizes by severity (Critical 90+ days, Severe 30+ days)
  - Lists top 10 delinquent loans
  - Notification type: `system_alert`

**Usage**:
```bash
python manage.py send_admin_overdue_alerts
```

**Cron Setup** (recommended: daily):
```bash
0 10 * * * cd /path/to/banking-system && python manage.py send_admin_overdue_alerts
```

### 5. Admin Alerts for System Updates ✅
- **Location**: `notifications/management/commands/send_system_update_alerts.py`
- **Functionality**: Sends alerts to admins about system updates, maintenance, or security patches
- **Details**:
  - Supports different alert types: maintenance, security, update, general
  - Can be customized with custom subject and message
  - Notification type: `system_alert`

**Usage**:
```bash
# Default general alert
python manage.py send_system_update_alerts

# Custom message
python manage.py send_system_update_alerts --message "Security patch available" --subject "Security Update Required" --type security

# Maintenance alert
python manage.py send_system_update_alerts --type maintenance --message "Scheduled maintenance on Saturday 2AM-4AM"
```

## Notification Types

The system supports the following notification types:
- `payment_reminder` - Payment reminders for borrowers
- `loan_approved` - Loan approval notifications
- `due_date` - Due date reminders
- `system_alert` - System alerts for admins

## Notification Channels

### Email ✅
- Uses Django's `send_mail` function
- Configured via `settings.DEFAULT_FROM_EMAIL`
- Records sent status in database

### SMS (Mocked) ✅
- Currently logs SMS messages (for development)
- Ready for integration with SMS gateway (Twilio, Chikka, etc.)
- Records sent status in database

## Notification Management

### Viewing Notifications
- **URL**: `/notifications/`
- **Access**: All authenticated users
- **Features**:
  - Filter by type, status, date range
  - View notification history
  - See sent/failed status

### Sending Manual Notifications (Admin/Staff)
- **URL**: `/notifications/` (use "Send Notification" button)
- **Access**: Admin and Staff only
- **Features**:
  - Select recipient
  - Choose notification type
  - Custom subject and message

## Database Model

Notifications are stored in the `Notification` model with:
- User (recipient)
- Type (email/sms)
- Notification type (payment_reminder, loan_approved, etc.)
- Subject and message
- Related entity (loan, account, system)
- Sent date and status

## Scheduled Tasks Setup

For production, set up cron jobs:

```bash
# Edit crontab
crontab -e

# Add these lines (adjust paths):
# Daily payment reminders at 9 AM
0 9 * * * cd /path/to/banking-system && /path/to/venv/bin/python manage.py send_due_date_reminders

# Daily admin overdue alerts at 10 AM
0 10 * * * cd /path/to/banking-system && /path/to/venv/bin/python manage.py send_admin_overdue_alerts
```

## Integration Points

1. **Loan Approval**: Automatically sends notification when loan is approved
2. **Loan Rejection**: Automatically sends notification when loan is rejected
3. **Loan Disbursement**: Automatically sends notification when funds are disbursed
4. **Payment Reminders**: Scheduled daily via cron
5. **Admin Alerts**: Can be scheduled or run manually

## Future Enhancements

- [ ] Integrate real SMS gateway (Twilio, Chikka)
- [ ] Push notifications for mobile app
- [ ] Notification preferences per user
- [ ] Email templates with HTML formatting
- [ ] Notification digest (daily/weekly summary)


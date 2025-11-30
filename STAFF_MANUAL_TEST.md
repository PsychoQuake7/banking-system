# Staff User Manual Verification Checklist

## Login & Authentication
- [ ] Logout current user
- [ ] Login as staff user (maria.santos / password123)
- [ ] Verify staff dashboard loads
- [ ] Check staff-specific permissions

## Client Management
- [ ] Navigate to Clients page
- [ ] Test search: search for "Test"
- [ ] Test status filter: select "active"
- [ ] Test credit score filter: select "excellent"
- [ ] Clear filters
- [ ] Click on a client to view details
- [ ] Test client creation form
- [ ] Test client edit form

## Account Management  
- [ ] Navigate to Accounts page
- [ ] View account list
- [ ] Click on an account to view details
- [ ] Test account creation (if accessible)
- [ ] Verify balance displays correctly

## Transaction Management
- [ ] Navigate to Transactions page
- [ ] Test transaction type filter: select "deposit"
- [ ] Test date range filter: set dates
- [ ] Test account filter: select an account
- [ ] Clear filters
- [ ] Create deposit transaction
- [ ] Create withdrawal transaction
- [ ] Test insufficient funds (try withdrawing large amount)
- [ ] Test transfer form (THE BUG WE FIXED)

## Loan Management
- [ ] Navigate to Loan Applications page
- [ ] Test status filter: "pending"
- [ ] Test status filter: "approved"
- [ ] Test status filter: "rejected"
- [ ] Test date range filter
- [ ] Click on a loan to view details
- [ ] Test loan approval (if pending loans exist)
- [ ] Test loan rejection

## Audit Logs
- [ ] Navigate to Audit Logs page
- [ ] Verify logs are visible
- [ ] Test action filter
- [ ] Test user filter
- [ ] Test date range filter

## Notifications
- [ ] Navigate to Notifications page
- [ ] View notification list
- [ ] Test mark as read (if available)

## Edge Cases & Validations
- [ ] Try submitting empty forms
- [ ] Try invalid inputs
- [ ] Test negative numbers
- [ ] Test decimal precision
- [ ] Test required field validations

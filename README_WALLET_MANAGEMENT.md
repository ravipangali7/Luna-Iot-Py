# Wallet Management System

## Overview
The Luna IoT system now includes a comprehensive wallet management system that automatically creates wallets for users and provides administrative tools for managing wallet balances.

## Features

### Backend Features
- **Automatic Wallet Creation**: Wallets are automatically created with 0 balance when users register or are created by admins
- **Wallet Model**: Complete wallet model with balance tracking, user association, and timestamps
- **API Endpoints**: Full CRUD API for wallet management
- **Management Command**: Script to create missing wallets for existing users

### Frontend Features
- **User Management**: Complete CRUD interface for managing users
- **Wallet Management**: Interface for viewing and editing user wallet balances
- **User Reports**: Detailed user information including wallet balance and permissions
- **Finance Section**: New sidebar section for financial management

## Management Command

### Create Missing Wallets Command

The system includes a Django management command to create wallets for users who don't have one:

```bash
# Create wallets for all users without one
python manage.py create_missing_wallets

# Dry run to see what would be created (recommended first)
python manage.py create_missing_wallets --dry-run

# Process in smaller batches (default is 100)
python manage.py create_missing_wallets --batch-size 50
```

#### Command Options
- `--dry-run`: Shows what would be done without actually creating wallets
- `--batch-size N`: Number of wallets to create in each batch (default: 100)

#### Example Output
```
Starting wallet creation process...
Found 25 users without wallets
DRY RUN MODE - No wallets will be created

Users who would get wallets:
--------------------------------------------------
ID: 1, Name: John Doe, Phone: +1234567890
ID: 2, Name: Jane Smith, Phone: +1234567891
... and 15 more users
```

## API Endpoints

### Wallet Endpoints
- `GET /api/core/wallet/wallets` - Get all wallets
- `GET /api/core/wallet/wallet/user/<user_id>` - Get wallet by user
- `GET /api/core/wallet/wallet/<wallet_id>` - Get wallet by ID
- `POST /api/core/wallet/wallet/create` - Create new wallet
- `PUT /api/core/wallet/wallet/<wallet_id>` - Update wallet balance
- `PUT /api/core/wallet/wallet/<wallet_id>/balance` - Balance operations (add/subtract/set)
- `DELETE /api/core/wallet/wallet/<wallet_id>` - Delete wallet

### User Endpoints
- `GET /api/core/user/users` - Get all users
- `GET /api/core/user/user/<phone>` - Get user by phone
- `POST /api/core/user/user/create` - Create new user
- `PUT /api/core/user/user/<phone>` - Update user
- `DELETE /api/core/user/user/<phone>` - Delete user

## Frontend Routes

### User Management
- `/users` - User list page
- `/users/create` - Create user page
- `/users/:id` - User detail page
- `/users/:id/edit` - Edit user page

### Wallet Management
- `/wallet` - Wallet management page

## Database Schema

### Wallet Model
```python
class Wallet(models.Model):
    id = models.BigAutoField(primary_key=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Usage Instructions

### For Administrators

1. **Access User Management**:
   - Navigate to Users → User Management in the sidebar
   - View, create, edit, or delete users
   - Each user automatically gets a wallet with 0 balance

2. **Access Wallet Management**:
   - Navigate to Finance → Wallet Management in the sidebar
   - View all user wallets and their balances
   - Edit wallet balances using the edit button
   - Use operations: Add, Subtract, or Set balance

3. **View User Reports**:
   - Click on any user in the user list
   - View detailed user information including wallet balance
   - See user roles, permissions, and associated vehicles

### For Developers

1. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Create Missing Wallets** (if needed):
   ```bash
   python manage.py create_missing_wallets --dry-run
   python manage.py create_missing_wallets
   ```

3. **Access Admin Interface**:
   - Wallets are available in Django admin
   - View and manage wallets through the admin interface

## Security

- All wallet operations require authentication
- Only Super Admin users can access wallet management
- Balance operations are validated to prevent negative balances
- All API endpoints include proper error handling

## Error Handling

- Comprehensive error handling in both frontend and backend
- User-friendly error messages
- Validation for all wallet operations
- Transaction safety for balance updates

## Future Enhancements

- Transaction history for wallets
- Wallet-to-wallet transfers
- Payment integration
- Automated billing based on wallet balance
- Wallet notifications and alerts

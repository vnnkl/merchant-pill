# the migration file is where you build your database tables
# If you create a new release for your extension , remember the migration file is like a blockchain, never edit only add!

async def m001_initial(db):
    """
    Initial templates table.
    """
    await db.execute(
        """
        CREATE TABLE merchantpill.maintable (
            id TEXT PRIMARY KEY,
            wallet TEXT NOT NULL,
            name TEXT NOT NULL,
            total INTEGER DEFAULT 0,
            lnurlpayamount INTEGER DEFAULT 0,
            lnurlwithdrawamount INTEGER DEFAULT 0,
            lnurlwithdraw TEXT,
            lnurlpay TEXT
        );
    """
    )

# Here we add another field to the database

async def m002_addtip_wallet(db):
    """
    Add total to templates table
    """
    await db.execute(
        """
        ALTER TABLE merchantpill.maintable ADD ticker INTEGER DEFAULT 1;
    """
    )

async def m003_add_debt_table(db):
    """
    Add debt table
    """
    await db.execute(
        """
        CREATE TABLE merchantpill.debt (
            id TEXT PRIMARY KEY,
            inviter_id TEXT,
            inviterWallet TEXT,
            debtPaid INTEGER DEFAULT 0,
            debtOutstanding INTEGER DEFAULT 0,
            debtCurrency TEXT,
            FOREIGN KEY(inviter_id) REFERENCES merchantpill.maintable(id)
        );
        """
    )

async def m004_add_transaction_table(db):
    """
    Add transaction table
    """
    await db.execute(
        """
        CREATE TABLE merchantpill.transaction (
            id TEXT PRIMARY KEY,
            from_user_id TEXT,
            to_user_id TEXT,
            amount INTEGER DEFAULT 0,
            currency TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(from_user_id) REFERENCES merchantpill.maintable(id),
            FOREIGN KEY(to_user_id) REFERENCES merchantpill.maintable(id)
        );
        """
    )

async def m005_add_fields_to_user_table(db):
    """
    Add invited_by and debt_id fields to user table
    """
    await db.execute(
        """
        ALTER TABLE merchantpill.maintable ADD invited_by TEXT;
        ALTER TABLE merchantpill.maintable ADD debt_id TEXT;
        """
    )

# Unit of Work pattern implementation for database transactions
class UnitOfWork:
    def __init__(self, session_factory):
        # Store factory function to create new sessions
        self.session_factory = session_factory
        
    def __enter__(self):
        # Create new session when entering context
        self.session = self.session_factory()
        return self.session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Handle transaction completion
        if exc_type is not None:
            # Rollback on exception
            self.session.rollback()
        else:
            # Commit if successful
            self.session.commit()
        # Always close the session
        self.session.close() 
import ctypes
import sys

class AdminHandler:

    @staticmethod
    def is_admin(): 
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def check_and_request_admin():
        """Check if running as admin. If not, request elevation and exit."""
        if not AdminHandler.is_admin():
            print("This application requires administrator privileges to run.")
            print("Do you consent to run the application as an administrator? (y/n): ", end="")
            choice = input().strip().lower()
            if choice == 'n':
                print("Exiting application.")
                sys.exit(1)
            elif choice == 'y':
                print("Relaunching application with administrator privileges...")
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit(0)
            else:
                print("Invalid choice. Exiting application.")
                print("Enter 'Y' to consent or 'N' to decline.")
                sys.exit(1)

    def get_status(self):
        """Get the current admin status."""
        return AdminHandler.is_admin()

    def set_status(self, status):
        """Set or enforce admin status."""
        if not status and AdminHandler.is_admin():
            print("Admin privileges are required for this application.")
            return False
        return True
            
        
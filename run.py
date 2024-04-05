from SimplyStars import app
from SimplyStars.NetworkController import main, check_credentials
from SimplyStars.AccountController import accounts

if __name__ == '__main__':
    # Check if we have valid credentials first
    creds = check_credentials()
    
    # If credentials are invalid, run the OAuth flow
    if not creds:
        main()

    # Now start the Flask app
    
    app.run(host='0.0.0.0', debug=True)

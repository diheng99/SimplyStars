from SimplyStars import app
from SimplyStars.gmailAPI import main

if __name__ == '__main__':
    main()
    app.run(host='0.0.0.0', debug=True)
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()
test_mode = os.getenv('TEST_MODE')

if __name__ == '__main__':
    if test_mode not in ['True', 'False']:
        print('TEST_MODE env variable not set properly!')
    else:
        uvicorn.run(
            app='app.main:app', 
            host='127.0.0.1', 
            port=8000, 
            reload=True,
            reload_excludes=[
                'app/tests/conftest.py',
                'app/tests/test_root.py',
                'app/tests/test_users_router.py',
                'app/tests/test_books_router.py'
                ]
            )
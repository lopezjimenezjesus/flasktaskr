import os
import unittest

from project import app, db
from project._config import basedir
from project.models import Task, User

TEST_DB = 'test.db'

class AllTest(unittest.TestCase):

    # Setup and teardown

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
            os.path.join(basedir, TEST_DB)
        self.app = app.test_client()
        db.create_all()

    # executed after each test_client
    def tearDown(self):
        db.session.remove()
        db.drop_all()

    ########################
    #### helper methods ####
    ########################

    def login(self, name, password):
        return self.app.post('/', data=dict(
            name=name, password=password), follow_redirects=True)

    def register(self, name, email, password, confirm):
        return self.app.post(
            'register/',
            data=dict(name=name, email=email, password=password,
                      confirm=confirm),
            follow_redirects=True
        )

    def create_user(self, name, email, password):
        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()


    def logout(self):
        return self.app.get('logout/', follow_redirects=True)


    def create_task(self):
        return self.app.post('add/', data=dict(
            name='Go to the bank',
            due_date='02/05/2014',
            priority=1,
            posted_date='02/04/2014',
            status='1'
        ), follow_redirects=True)

    # test

    def test_users_can_add_tasks(self):
        self.create_user('Michael',
                         'michael@realpython.com',
                         'python')
        self.login('Michael', 'python')
        self.app.get('tasks/', follow_redirects=True)
        response = self.create_task()
        self.assertIn(b'New entry was succesfully posted. Thanks.',
                      response.data)

    def test_users_cannot_add_tasks_when_error(self):
        self.create_user('Michael',
                         'michael@realpython.com',
                         'python')
        self.login('Michael', 'python')
        self.app.get('tasks/', follow_redirects=True)
        response = self.app.post('add/', data=dict(
            name='Go to the bank',
            due_date='',
            priority='1',
            posted_date='02/05/2014',
            status='1'
        ), follow_redirects=True)
        self.assertIn(b'This field is required.', response.data)

    def test_users_can_complete_tasks(self):
        self.create_user('Michael', 'michael@realpython',
                         'python')
        self.login('Michael', 'python')
        self.app.get('tasks/', follow_redirects='True')
        self.create_task()
        response = self.app.get("complete/1", follow_redirects=True)
        self.assertIn(b'The task is complete. Nice.', response.data)

    def test_users_can_delete_tasks(self):
        self.create_user('Michael', 'michael@realpython',
                         'python')
        self.login('Michael', 'python')
        self.app.get('tasks/', follow_redirects='True')
        self.create_task()
        response = self.app.get("delete/1", follow_redirects=True)
        self.assertIn(b'The task was deleted.', response.data)

    def tests_users_cannot_complete_tasks_that_are_not_created_by_them(self):
        self.create_user('Michael', 'michael@realpython',
                         'python')
        self.login('Michael', 'python')
        self.app.get('tasks/', follow_redirects='True')
        self.create_task()
        self.logout()
        self.create_user('Fletcher', 'fletcher@realpython',
                         'python101')
        self.login('Fletcher', 'python101')
        self.app.get('tasks/', follow_redirects=True)
        response = self.app.get('complete/1', follow_redirects=True)
        self.assertNotIn(b'The task is complete. Nice.', response.data)
        self.assertIn(
            b'You can only update tasks that belong to you.', response.data
        )

    def test_users_cannot_delete_tasks_that_are_not_created_by_them(self):
        self.create_user('Michael', 'michael@realpython.com', 'python')
        self.login('Michael', 'python')
        self.app.get('tasks/', follow_redirects=True)
        self.create_task()
        self.logout()
        self.create_user('Fletcher', 'fletcher@reappython.com', 'python101')
        self.login('Fletcher', 'python101')
        self.app.get('tasks/', follow_redirects=True)
        response = self.app.get("delete/1", follow_redirects=True)
        self.assertIn(
            b'You can only delete tasks that belong to you.',
            response.data
        )

if __name__ == '__main__':
    unittest.main()
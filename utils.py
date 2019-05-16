# -*- coding: utf-8 -*-
import os, sys
import shutil
import logging
import boto3

# for sending e-mail to user
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# for logging
from logging.handlers import RotatingFileHandler

def create_dir(directory):
    '''
    create directory if not exist
    '''
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            shutil.rmtree(directory)
            os.makedirs(directory)

    except OSError:
        model_logger.error('Error: Creating directory {} '.format(directory))

def is_file_zero(file):
    return True if os.path.getsize(file) == 0 else False

def send_sqs_message(directory):
    '''
    send Amazon SQS message to the cloud
    '''
    sqs = boto3.resource('sqs', region_name='us-east-1')
    queue = sqs.get_queue_by_name(QueueName='bart-web')
    response = queue.send_message(MessageBody='BART submission', MessageAttributes={
        'submission': {
            'StringValue': directory,
            'DataType': 'String'
        }
    })


def send_email(user_mail, user_key, email_type):
    '''
    send user job key to e-mail according to different type.

    email_type:
    - Submit: when user submits a job
    - Done: when job finishes successfully
    - Error: when job finishes with an error
    '''

    # TODO: encryot
    HOST_ADDRESS = "zanglab.service@gmail.com"
    PASSWORD = "ZangLab2018"

    msg = MIMEMultipart()
    msg['From'] = HOST_ADDRESS
    msg['To'] = user_mail

    message = ""
    # === when user submits a job
    if email_type == 'Submit':
        msg['Subject'] = "BART key"
        # better change to a file template later
        message = '''
Hi there,

Thank you for using BART web!

Here is your key: {}

When the job is done, you can ge the results through this link: {}
'''.format(user_key, 'http://bartweb.org/result?user_key='+user_key)

    # === when job finishes successfully
    if email_type == 'Done':
        msg['Subject'] = "BART result"
        message = '''
Congratulations! Your BART job is done!

Please get the results through this link: {}
'''.format('http://bartweb.org/result?user_key='+user_key)

    # === when job finishes with an error
    if email_type == 'Error':
        msg['Subject'] = "BART error"
        message = '''
Unfortunately, your BART job ends with errors.

Please check whether you chose the correct species or uploaded the required format file.

Or reach us at wm9tr@virginia.edu with your key: {}

'''.format(user_key)

    msg.attach(MIMEText(message, 'plain'))
    server = smtplib.SMTP_SSL("smtp.gmail.com")
    try:
        server.login(HOST_ADDRESS, PASSWORD)
        msg = msg.as_string()
        server.sendmail(HOST_ADDRESS, user_mail, msg)
    except smtplib.SMTPAuthenticationError:
        return False, "username or password is wrong"
    except:
        return False, "errors in sending key to e-mail..."
    finally:
        server.quit()  # finally close the connection with server

    return True, "send e-mail to user successfully..."


# === log related ===
# Debug mode or not
DebugConf = True
#DebugConf = False

# Init Loggers and Log Handlers
model_logger = logging.getLogger('bartweb-logger')
formatter = logging.Formatter('[%(asctime)s][pid:%(process)s-tid:%(thread)s] %(module)s.%(funcName)s: %(levelname)s: %(message)s')

# StreamHandler for print log to console
hdr = logging.StreamHandler()
hdr.setFormatter(formatter)
hdr.setLevel(logging.DEBUG)

# RotatingFileHandler
## Set log dir
abs_path = os.path.dirname(os.path.abspath(__file__))
log_dir_path = abs_path + '/log'
if not os.path.exists(log_dir_path):
    os.makedirs(log_dir_path)

## Specific file handler, split at 10MB
fhr_model = RotatingFileHandler('%s/bartweb.log'%(log_dir_path), maxBytes=10*1024*1024, backupCount=3)
fhr_model.setFormatter(formatter)
fhr_model.setLevel(logging.DEBUG)

# Add Handlers
model_logger.addHandler(fhr_model)
if DebugConf:
    model_logger.addHandler(hdr)
    model_logger.setLevel(logging.DEBUG)
else:
    model_logger.setLevel(logging.ERROR)

if __name__ == '__main__':
    '''
    Usage:
    from tools.log_tools import data_process_logger as logger
    logger.debug('debug debug')
    '''
    model_logger.info('Ohhh model')
    model_logger.error('error model')

# -*- coding: utf-8 -*-
import os
import yaml
from flask import (Flask, flash, request, redirect, url_for, render_template, send_from_directory, session)
from werkzeug.utils import secure_filename

import parseIO
from utils import model_logger as logger

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

# related to flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# === index page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # submit job button
        if 'submit_button' in request.form:
            # use user email or job name to generate unique job path
            username = request.form['username']
            jobname = request.form['jobname']
            user_key = parseIO.generate_user_key(username, jobname)

            # docker user path
            user_path = parseIO.init_project_path(user_key)

            # init user data
            user_data = {}
            user_data['user_email'] = username
            user_data['user_job'] = jobname
            user_data['user_key'] = user_key
            user_data['user_path'] = user_path
            user_data['dataType'] = request.form['dataType']
            user_data['assembly'] = request.form['species']
            user_data['files'] = ""

            if user_data['dataType'] == "ChIP-seq":
                allowed_extensions = set(['bam', 'bed'])
            if user_data['dataType'] == "Geneset":
                allowed_extensions = set(['txt'])

            # get pasted genes and save to upload/genelist.txt
            if request.form.get('uploadList', None):
                gene_list = request.form['uploadList']
                gene_list_file = 'Geneset.txt'
                gene_list_file_path = os.path.join(user_path, 'upload/' + gene_list_file)
                with open(gene_list_file_path, 'w') as fopen:
                    for gene in gene_list:
                        fopen.write(gene)
                user_data['files'] = gene_list_file

            # validate upload file and write fine name and file path into config in the case of profile input
            if request.form['dataType'] == 'ChIP-seq':	
                # process what user has uploaded	
                if 'uploadFilesProfile' not in request.files:	
                    flash('Please choose a file')	
                    return redirect(request.url)	
                file = request.files['uploadFilesProfile']
                # if user does not select file, browser also submits an empty part without filename	
                if file.filename == '':	
                    flash('One of the files does not have a legal file name.')	
                    return redirect(request.url)
                # make sure the suffix of filename in [.txt, .bam, .bed]
                datatype = request.form['dataType']
                if file and allowed_file(file.filename, allowed_extensions):	
                    filename = secure_filename(file.filename)	
                    upload_path = os.path.join(user_path, 'upload')	
                    ext = filename.split('.')[-1]
                    filename = "ChIP_seq."+ext
                    filename_abs_path = os.path.join(upload_path, filename)	
                    file.save(filename_abs_path)	
                    user_data['files'] = filename # only save file name, since the uploaded path is always the same
            
            # validate upload file and write fine name and file path into config in the case of genelist input
            if request.form['dataType'] == 'Geneset' and request.form['geneType'] == 'geneFile': 
                # process what user has uploaded    
                if 'uploadFilesGenelist' not in request.files:  
                    flash('Please choose a file')   
                    return redirect(request.url)    
                file = request.files['uploadFilesGenelist']
                # if user does not select file, browser also submits an empty part without filename 
                if file.filename == '': 
                    flash('One of the files does not have a legal file name.')  
                    return redirect(request.url)
                # make sure the suffix of filename in [.txt, .bam, .bed]
                datatype = request.form['dataType']
                if file and allowed_file(file.filename, allowed_extensions):    
                    filename = secure_filename(file.filename)   
                    upload_path = os.path.join(user_path, 'upload') 
                    filename = "Geneset.txt"
                    filename_abs_path = os.path.join(upload_path, filename)   
                    file.save(filename_abs_path)    
                    user_data['files'] = filename # only save file name, since the uploaded path is always the same

            parseIO.init_user_config(user_path, user_data)
            parseIO.prepare_bart(user_data)
            return redirect(url_for('get_result', user_key=user_key))

        # get result button
        if 'result_button' in request.form:
            user_key = request.form['result_button']
            # when key is null, refresh the website
            if user_key == "":
                return render_template('index.html')

            logger.info("Retrieve result: for " + user_key)

            if parseIO.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")

                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")

                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))

        # navbar result button
        if 'navbar_button' in request.form:
            logger.info("Retrieve result...")
            user_key = request.form['navbar_button']  

            if parseIO.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")
                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))
    return render_template('index.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # navbar result button
        if 'navbar_button' in request.form:
            logger.info("Retrieve result...")
            user_key = request.form['navbar_button']  

            if parseIO.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: can not find the result for {}.".format(user_key))
                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))

    return render_template('contact.html')

@app.route('/help', methods=['GET', 'POST'])
def help():
    if request.method == 'POST':
        # navbar result button
        if 'navbar_button' in request.form:
            logger.info("Retrieve result...")
            user_key = request.form['navbar_button']  

            if parseIO.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")
                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))

    return render_template('help.html')

#############################################

@app.route('/result', methods=['GET', 'POST'])
def get_result():
    if request.method == 'POST':
        # navbar result button
        if 'navbar_button' in request.form:
            logger.info("Retrieve result...")
            user_key = request.form['navbar_button']  

            if parseIO.is_user_key_exists(user_key):
                logger.info("Retrieve result: user exists.")
                return redirect(url_for('get_result', user_key=user_key))
            else:
                logger.error("Retrieve result: did not find the result.")
                err_msg = "Job does not exist, make sure you enter the right key."
                return redirect(url_for('error_page', msg=err_msg))

    else:
        user_key = request.args['user_key']
        user_data = parseIO.get_user_data(user_key)

        logger.info('Get result: for ' + user_key)
        logger.info(user_data)

        results = parseIO.generate_results(user_data)
        results['sample'] = False
        return render_template('result_demonstration.html', results=results, key=request.args['user_key'])

@app.route('/error', methods=['GET', 'POST'])
def error_page():
    err_msg = request.args['msg']
    return render_template('error.html', msg=err_msg)

@app.route('/plot/<userkey_tfname>')
def bart_plot_result(userkey_tfname):
    user_key, tf_name = userkey_tfname.split('___')
    # ========= using d3.js below=============
    # use user_key to retrieve plot related results
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    bart_output_dir = os.path.join(user_path, 'download/')

    plot_results = parseIO.generate_plot_results(bart_output_dir, tf_name)
    return render_template('plot_result.html', plotResults=plot_results)

@app.route('/log/<userkey_filename>')
def download_log_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    log_path = os.path.join(user_path, 'log')
    return send_from_directory(log_path, filename)

@app.route('/download/<userkey_filename>')
def download_result_file(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'usercase/' + user_key)
    download_path = os.path.join(user_path, 'download')
    return send_from_directory(download_path, filename)

# ===== for genelist/ChIPdata sample =====




# download sample data
@app.route('/sample/<sample_type>')
def download_sample_file(sample_type):
    sample_path = ""
    sample_name = ""
    if sample_type == 'genelist':
        sample_name = "genelist.txt"
        sample_path = os.path.join(PROJECT_DIR, 'sample/genelist/upload')
    elif sample_type == 'ChIPdata':
        sample_name = "ChIPseq.txt"
        sample_path = os.path.join(PROJECT_DIR, 'sample/ChIPdata/upload')

    return send_from_directory(sample_path, sample_name)

# sample result
@app.route('/sample_result/<sample_type>')
def sample_result(sample_type):
    config_file = os.path.join(PROJECT_DIR, 'sample/' + sample_type + '/user.config')
    if not os.path.exists(config_file):
        return None

    user_data = {}
    with open(config_file, 'r') as fopen:
        user_data = yaml.load(fopen)

    if user_data:
        results = parseIO.generate_results(user_data)
        
        if 'bart_result_files' in results:
            bart_result_list = []
            for bart_res_file in results['bart_result_files']:
                filename, file_url = bart_res_file
                bart_result_list.append((filename, file_url.replace('download', 'sample_download')))
            results['bart_result_files'] = bart_result_list

    results['sample'] = True
    results['sample_type'] = sample_type
    return render_template('result_demonstration.html', results=results)

# show sample plot result
@app.route('/sample_plot/<sample_type>/<tf_name>')
def bart_sample_plot_result(sample_type, tf_name):
    user_path = os.path.join(PROJECT_DIR, 'sample/' + sample_type)
    bart_output_dir = os.path.join(user_path, 'download')

    plot_results = parseIO.generate_plot_results(bart_output_dir, tf_name)
    return render_template('plot_result.html', plotResults=plot_results)

# download sample result files
@app.route('/sample_download/<userkey_filename>')
def download_sample_result(userkey_filename):
    user_key, filename = userkey_filename.split('___')
    user_path = os.path.join(PROJECT_DIR, 'sample/' + user_key)
    download_path = os.path.join(user_path, 'download')
    return send_from_directory(download_path, filename)


def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')

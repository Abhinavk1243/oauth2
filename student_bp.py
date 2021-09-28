from datetime import datetime
from flask import Blueprint,render_template,redirect,url_for,request,jsonify,flash,session
from commons import mysl_pool_connection,logger
import pandas as pd
from app import oauth
# from model import db,User,Client,Token,Grant

pool_cnxn=mysl_pool_connection("mysql_web_data")
mycursor=pool_cnxn.cursor()
logger=logger()

student_bp=Blueprint("student_bp",__name__,template_folder="templates")

@student_bp.route("/",methods=["GET"])
@oauth.require_oauth()
def get_student():
    if request.args:            
        mycursor=pool_cnxn.cursor()
        query_params_dict=request.args.to_dict()
        sql="select * from  web_data.student " 
        no_of_cond=0
        for i in list(query_params_dict.keys()):
            if no_of_cond==0:
                if (query_params_dict[i]).isalpha:
                    sql=sql+f"  where {i}='{query_params_dict[i]}' "
                else:
                    sql=sql+f" and {i}=int({query_params_dict[i]})"
                no_of_cond=1
            else:
                if (query_params_dict[i]).isalpha:
                    sql=sql+f" and {i}='{query_params_dict[i]}' "
                else:
                    sql=sql+f" and {i}=int({query_params_dict[i]})"
        try:
            mycursor.execute(sql)
            student=mycursor.fetchall()
        except Exception as error:
            return jsonify({"error":"internal server error"}),500
        if student==[]:
            message=f"error :'record at {query_params_dict} not found '"
            return jsonify({"error":message}),400
        else:
            # if request.content_type=="application/json":
            df=pd.read_sql(con=pool_cnxn, sql=sql)
            student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
            response={"response":{"method":"GET","Status_Code":200,"description":"return record of student","data":student}}
            return jsonify(response)   
            # return render_template("student.html",**locals())         
    else:
        sql="select * from  web_data.student "
        # if request.content_type=="application/json":
        df=pd.read_sql(con=pool_cnxn, sql=sql)
        student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
        response={"response":{"method":"GET","Status_Code":200,"description":"return record of student","data":student}}
        return jsonify(response)  ,200
    
@student_bp.route("/",methods=["POST"])
@oauth.require_oauth()
def create_student():  
    student_data=request.get_json(force=True)
    mycursor=pool_cnxn.cursor()  
    try:
        
        student_name=student_data['student_name']
        student_age=student_data['student_age']
    except KeyError as error:
        example_data={"student_name":"name","student_age":54}
        return jsonify({"error":"data contain wrong keys","sample_data":example_data}),400

    val=(student_name,student_age)
    try:
        sql=f"insert into web_data.student(student_name, student_age) values {val}"
        mycursor.execute(sql)
        pool_cnxn.commit()
        logger.debug(f"data {val} successfully inserted")
        print("data inserted")
    except Exception as error:
        logger.error(f"exception arise : {error}")
        # print(f"Exception arise : {error}")
        return jsonify({"error":"internal server error"}),500
    df=pd.read_sql(con=pool_cnxn, sql='SELECT * FROM web_data.student ORDER BY student_id DESC LIMIT 1')
    student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
    return jsonify(student[0])

@student_bp.route("/",methods=['DELETE'])
@oauth.require_oauth()
def remove_student():
    if request.method=='DELETE':        
        mycursor=pool_cnxn.cursor()
        try:
            student_data=request.get_json(force=True)
            student_id=student_data["student_id"]
        except KeyError as error:
            return jsonify({"error":"key error in data","sample_data":{"student_id":34}}),500
        sql=f"""select student_id,student_name,student_age from web_data.student where student_id={student_id}"""
        df=pd.read_sql(con=pool_cnxn, sql=sql)
        student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
        if student==[]:
            error=f"student with id {student_id} not exist"
            return jsonify({"error":error}),400
        try:
            sql=f"delete from  web_data.student where student_id={student_id} "
            mycursor.execute(sql)
            pool_cnxn.commit()            
            logger.debug(f"record of id = {id} is deleted from the database")
        except Exception as error:
            logger.error(f"exception arise : {error}")
            print(f"Exception arise : {error}")
            return jsonify({"error":"internal server error"}),500             
    return jsonify({"response":"student is successfully removed from database","removed_student_record":student})

@student_bp.route("/",methods=["PUT"])
@oauth.require_oauth()
def student_update(): 
    mycursor=pool_cnxn.cursor()
    student_data=request.get_json(force=True)
    try:
        student_name=student_data["student_name"]
        student_age=student_data['student_age']
        student_id=student_data['student_id']
        logger.debug(student_id)
    except Exception as error:
        logger.error(error)
        return jsonify({"error":error})
    mycursor.execute(f"select student_id from web_data.student where student_id={student_id}")
    if mycursor.fetchone()==None:
        error=f"student with id {student_id} not exist"
        return jsonify({"error":error}),400
    try:
        sql=f"""update web_data.student set student_name='{student_name}',
        student_age={student_age} where student_id={student_id}"""
        mycursor.execute(sql)
        pool_cnxn.commit()
        print(f"Data updatated successfully")
    except Exception as error:
        logger.error(f"error arise : {error}")
        return jsonify({"error":"internal server error"})
    df=pd.read_sql(con=pool_cnxn, sql=f'SELECT * FROM web_data.student where student_id={student_id}')
    student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
    res={"response_msg":"student record successfully updated",
        "data":student[0]}
    return jsonify(res)

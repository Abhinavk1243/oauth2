from datetime import datetime
from flask import Blueprint, json,render_template,redirect,url_for,request,jsonify,flash,session
from commons import mysql_pool_connection,logger
import pandas as pd
from app import oauth

pool_cnxn=mysql_pool_connection("mysql_web_data")
mycursor=pool_cnxn.cursor()
logger=logger()

employee_bp=Blueprint("employee_bp",__name__,template_folder="templates")
table="employee"

@employee_bp.route("/",methods=["GET"])
@oauth.require_oauth()
def get_employee():
    sql=f"select * from  web_data.{table} " 
    if request.args:            
        mycursor=pool_cnxn.cursor()
        query_params_dict=request.args.to_dict()
        
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
            employee = mycursor.fetchall()
        except Exception as error:
            return jsonify({"error":"internal server error"}),500
        if employee == []:
            message = f"error :'record at {query_params_dict} not found '"
            return jsonify({"error":message}),400
        else:
            df = pd.read_sql(con=pool_cnxn, sql=sql)
            employee = df.to_dict(orient="records")
            response = {"response":{"method":"GET","Status_Code":200,"description":"return record of employee","data":employee}}
            return jsonify(response)   
    
    else:
        df=pd.read_sql(con=pool_cnxn, sql=sql)
        employee = df.to_dict(orient="records")
        response={"response":{"method":"GET","Status_Code":200,"description":"return record of emplyee","data":employee}}
        return jsonify(response)  ,200


@employee_bp.route("/",methods=["POST"])
@oauth.require_oauth()
def create_employee():  
    data=request.get_json(force=True)
    mycursor=pool_cnxn.cursor()  
    try:
        employee_name = data["employee_name"]
        employee_age  = data["employee_age"]
        employee_salary  = data["employee_salary"]
    except KeyError as error:
        example={
                    "employee_age": 21,
                    "employee_name": "Caesar Vance",
                    "employee_salary": 106450
                }
        return jsonify({"error":"data contain wrong keys","sample_data":example}),400

    val=(employee_name,employee_age,employee_salary)
    try:
        sql=f"INSERT INTO web_data.{table}(employee_name,employee_age,employee_salary) values {val}"
        mycursor.execute(sql)
        pool_cnxn.commit()
        logger.debug(f"data {val} successfully inserted")
        
    except Exception as error:
        logger.error(f"exception arise : {error}")
        return jsonify({"error":"internal server error"}),500
    df=pd.read_sql(con=pool_cnxn, sql=f'SELECT * FROM web_data.{table} ORDER BY id DESC LIMIT 1')
    employee=df.to_dict(orient="record")
    return jsonify({"status":"success","data":employee[0]})

@employee_bp.route("/",methods=['DELETE'])
@oauth.require_oauth()
def remove_employee():
    if request.method=='DELETE':        
        mycursor=pool_cnxn.cursor()
        try:
            data=request.get_json(force=True)
            id=data["id"]
        except KeyError as error:
            return jsonify({"error":"key error in data","sample_data":{"id":34}}),500
        sql=f"""select id,employee_name,employee_age,employee_salary from web_data.{table} where id={id}"""
        df=pd.read_sql(con=pool_cnxn, sql=sql)
        employee=df.to_dict(orient="records")
        if employee==[]:
            error=f"employee with id {id} not exist"
            return jsonify({"error":error}),400
        try:
            sql=f"delete from  web_data.{table} where id={id} "
            mycursor.execute(sql)
            pool_cnxn.commit()            
            logger.debug(f"record of id = {id} is deleted from the database")
        except Exception as error:
            logger.error(f"exception arise : {error}")
            print(f"Exception arise : {error}")
            return jsonify({"error":"internal server error"}),500            
    sql=f"""select id,employee_name,employee_age,employee_salary from web_data.{table} where id={id}""" 
    mycursor.execute(sql)
    if mycursor.fetchone()==None:
        return jsonify({"status": "success","message": "successfully! deleted Records"}),200
    else:
        return jsonify({"status":"not success","error":"internal server error"})

@employee_bp.route("/",methods=["PUT"])
@oauth.require_oauth()
def employee_update(): 
    mycursor=pool_cnxn.cursor()
    employee_data=request.get_json(force=True)
    try:
        employee_name=employee_data["employee_name"]
        employee_age=employee_data['employee_age']
        employee_salary=employee_data['employee_salary']
        id=employee_data["id"]
        # data={"employee_name":employee_name,"employee_age"
        logger.debug(id)
    except Exception as error:
        logger.error(error)
        return jsonify({"error":error})
    mycursor.execute(f"select id from web_data.employee where id={id}")
    if mycursor.fetchone()==None:
        error=f"employee with id {id} not exist"
        return jsonify({"error":error}),400
    try:
        sql=f"""update web_data.employee set employee_name='{employee_name}',
        employee_age={employee_age},employee_salary={employee_salary} where id={id}"""
        mycursor.execute(sql)
        pool_cnxn.commit()
        print(f"Data updatated successfully")
    except Exception as error:
        logger.error(f"error arise : {error}")
        return jsonify({"error":"internal server error"})
    
    res={"status":"success","response":"employee record successfully updated"}
        
    return jsonify(res)

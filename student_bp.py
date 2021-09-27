from datetime import datetime
from flask import Blueprint,render_template,redirect,url_for,request,jsonify,flash,session
from commons import mysl_pool_connection
import pandas as pd
from app import oauth,get_grant,get_client,gen_salt,get_token,set_grant,save_token
from model import db,User,Client,Token,Grant

pool_cnxn=mysl_pool_connection("mysql_web_data")
mycursor=pool_cnxn.cursor("mysql_web_data")

student_bp=Blueprint("student_bp",__name__,template_folder="templates")

@student_bp.route("/")
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
            response={"response":{"method":"GET","Status_Code":200,"description":"return record of student","student":student}}
            return jsonify(response)   
            # return render_template("student.html",**locals())         
    else:
        sql="select * from  web_data.student "
        # if request.content_type=="application/json":
        df=pd.read_sql(con=pool_cnxn, sql=sql)
        student = [{col:getattr(row, col) for col in df} for row in df.itertuples()]
        response={"response":{"method":"GET","Status_Code":200,"description":"return record of student","student":student}}
        return jsonify(response)  ,200
        # mycursor=pool_cnxn.cursor()
        # mycursor.execute(sql)
        # student=mycursor.fetchall()
        # return render_template("student.html",**locals())
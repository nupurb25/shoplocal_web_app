yum update -y
yum install python3 python3-pip git mariadb105 -y

cd /home/ec2-user

pip3 install -r requirements.txt

export DB_HOST=nupur-db.c18yme60g2po.us-west-2.rds.amazonaws.com
export DB_USER=nupur
export DB_PASSWORD=nupur123123
export DB_NAME=shoplocal
export SECRET_KEY=$(openssl rand -hex 16)

mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD < database_enhanced.sql

nohup python3 app.py > /var/log/shoplocal.log 2>&1 &

import MySQLdb

def connectDB():
	# Open database connection
	db = MySQLdb.connect("localhost","root","raspberry","pcounter" )

	return db
	# prepare a cursor object using cursor() method
	
def insert_log(db, a_b, b_a):
	cursor = db.cursor()

	# Prepare SQL query to INSERT a record into the database.
	sql = "INSERT INTO log(a_b,b_a) VALUES ('"+str(a_b)+"','"+str(b_a)+"')"
	try:
   		# Execute the SQL command
   		cursor.execute(sql)
   		# Commit your changes in the database
   		db.commit()
	except:
   		# Rollback in case there is any error
   		db.rollback()

def disconnect(db):
	# disconnect from server
	db.close()

db = connectDB()

insert_log(db,1,0)

disconnect(db)

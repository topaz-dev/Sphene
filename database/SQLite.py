import discord
import sqlite3 as sql
import datetime as dt
import time as t
import json
from core import welcome as wel


DB_NOM = 'SpheneDB'

def nom_ID(nom):
	"""Convertis un nom en ID discord """
	if len(nom) == 21 :
		ID = int(nom[2:20])
	elif len(nom) == 22 :
		ID = int(nom[3:21])
	else :
		print("DB >> mauvais nom")
		ID = -1
	return(ID)

#===============================================================================
# Ouverture du fichier DB
#===============================================================================
conn = sql.connect('database/{}.db'.format(DB_NOM))

#===============================================================================
# Initialisation et vérification de la DB
#===============================================================================
def init():
	# Liste des tables
	with open("database/DBlist.json", "r") as f:
		l = json.load(f)
	for one in l:
		# Ouverture du template de la table en cours
		with open("database/Templates/{}Template.json".format(one), "r") as f:
			t = json.load(f)
		cursor = conn.cursor()
		# Création du script
		script = "CREATE TABLE IF NOT EXISTS {}(".format(one)
		i = 0
		PRIMARYKEY = ""
		PRIMARYKEYlink = ""
		link = ""
		for x in t:
			if i != 0:
				script += ", "
			y = t[x].split("_")
			if len(y) > 1:
				if y[0] == "ID":
					script += "{0} {1} NOT NULL".format(x, y[1])
					link = "FOREIGN KEY(ID) REFERENCES IDs(ID)"
				elif y[0] == "PRIMARYKEY":
					script += "{0} {1} NOT NULL".format(x, y[1])
					PRIMARYKEY = "{}".format(x)
				elif y[0] == "link":
					script += "{0} INTEGER NOT NULL".format(x)
					PRIMARYKEYlink = "{}".format(x)
					link = "FOREIGN KEY({1}) REFERENCES {0}({1})".format(y[1], x)
			else:
				script += "{0} {1}".format(x, t[x])
			i += 1
		# Configuration des clés primaires
		if PRIMARYKEY != "" and PRIMARYKEYlink != "":
			script += ", PRIMARY KEY ({}, {})".format(PRIMARYKEY, PRIMARYKEYlink)
		elif PRIMARYKEY != "" and PRIMARYKEYlink == "":
			script += ", PRIMARY KEY ({})".format(PRIMARYKEY)
		elif PRIMARYKEY == "" and PRIMARYKEYlink != "":
			script += ", PRIMARY KEY ({})".format(PRIMARYKEYlink)
		if link != "":
			script += ", {}".format(link)
		script += ")"
		# éxécution du script pour la table en cours
		cursor.execute(script)
		conn.commit()
	# Quand toute les tables ont été créée (si elles n'existait pas), envoie un message de fin
	return "SQL >> DB initialisée"

#-------------------------------------------------------------------------------
def checkField():
	# Init de la variable flag
	flag = 0
	FctCheck = False
	while not FctCheck:
		try:
			FctCheck = True
			# Liste des tables
			with open("database/DBlist.json", "r") as f:
				l = json.load(f)
			for one in l:
				# Ouverture du template de la table en cours
				with open("database/Templates/{}Template.json".format(one), "r") as f:
					t = json.load(f)
				cursor = conn.cursor()
				# Récupération du nom des colonnes de la table en cours
				cursor.execute("PRAGMA table_info({0});".format(one))
				rows = cursor.fetchall()

				#Suppression
				for x in rows:
					if x[1] not in t:
						script = "ALTER TABLE {0} RENAME TO {0}_old".format(one)
						cursor.execute(script)
						init()
						cursor.execute("PRAGMA table_info({0}_old);".format(one))
						temp = ""
						for z in cursor.fetchall():
							if temp == "":
								temp += "{}".format(z[1])
							else:
								temp += ", {}".format(z[1])
						script = "INSERT INTO {0} ({1})\n	SELECT {1}\n	FROM {0}_old".format(one, temp)
						cursor.execute(script)
						cursor.execute("DROP TABLE {}_old".format(one))
						conn.commit()
						flag = "sup"+str(flag)

				#Type & add
				for x in t:
					check = False
					NotCheck = False
					y = t[x].split("_")
					for row in rows:
						if row[1] == x:
							if len(y) > 1:
								if row[2] == y[1]:
									check = True
								elif y[0] == "link":
									if row[2] == "INTEGER":
										check = True
									else:
										NotCheck = True
								else:
									NotCheck = True
							else:
								if row[2] == t[x]:
									check = True
								else:
									NotCheck = True
					if NotCheck:
						script = "ALTER TABLE {0} RENAME TO {0}_old".format(one)
						cursor.execute(script)
						init()
						cursor.execute("PRAGMA table_info({0}_old);".format(one))
						temp = ""
						for z in cursor.fetchall():
							if temp == "":
								temp += "{}".format(z[1])
							else:
								temp += ", {}".format(z[1])
						script = "INSERT INTO {0} ({1})\n	SELECT {1}\n	FROM {0}_old".format(one, temp)
						cursor.execute(script)
						cursor.execute("DROP TABLE {}_old".format(one))
						conn.commit()
						flag = "type"+str(flag)
					elif not check:
						if len(y) > 1:
							temp = y[1]
						else:
							temp = y[0]
						script = "ALTER TABLE {0} ADD COLUMN {1} {2}".format(one, x, temp)
						cursor.execute(script)
						flag = "add"+str(flag)
		except:
			FctCheck = False
	return flag


#===============================================================================
# Gestion des utilisateurs
#===============================================================================

#-------------------------------------------------------------------------------
def new(ID, nameDB):
	"""
	Permet d'ajouter un nouveau joueur à la base de donnée en fonction de son ID.

	ID: int de l'ID du serveur
	"""
	with open("database/Templates/{}Template.json".format(nameDB), "r") as f:
		t = json.load(f)

	one = valueAt(ID, "idGuild", nameDB)
	if one == "Error 404":
		data = "id{}".format(nameDB)
		values = str(ID)
		for x in t:
			if x != "id{}".format(nameDB) and x != "ID":
				data += ", {}".format(x)
				if "INTEGER" in t[x]:
					values += ", 0"
				else:
					values += ", NULL"
		script = "INSERT INTO {0} ({1}) VALUES ({2})".format(nameDB, data, values)
		# print("==== new ====")
		# print(script)
		cursor = conn.cursor()
		cursor.execute(script)
		conn.commit()
		return ("Le serveur a été ajouté !")
	else:
		return ("Le serveur existe déjà")


#===============================================================================
# Fonctions
#===============================================================================

#-------------------------------------------------------------------------------
def updateField(ID, fieldName, fieldValue, nameDB):
	"""
	Permet de mettre à jour la valeur fieldName par la fieldValue.

	ID: int de l'ID du serveur.
	fieldName: string du nom du champ à changer
	fieldValue: string qui va remplacer l'ancienne valeur
	"""
	cursor = conn.cursor()

	# Vérification que la donnée fieldName existe dans la table nameDB
	one = valueAt(ID, fieldName, nameDB)
	if one == "Eror 404":
		# print("DB >> Le champ n'existe pas")
		return "201"
	else:
		script = "UPDATE {0} SET {1} = '{2}' WHERE idGuild = '{3}'".format(nameDB, fieldName, fieldValue, ID)
		# print("==== updateField ====")
		# print(script)
		cursor.execute(script)
		conn.commit()
		return "200"

#-------------------------------------------------------------------------------
def valueAt(ID, fieldName, nameDB):
	"""
	Permet de récupérer la valeur contenue dans le champ fieldName de ID

	ID: int de l'ID du serveur
	fieldName: string du nom du champ à chercher
	"""
	cursor = conn.cursor()
	script = ""

	try:
		# Récupération de la valeur de fieldName dans la table nameDB
		script = 'SELECT {fn} FROM {ndb} WHERE idGuild = {guild}'.format(guild=ID, ndb=nameDB, fn=fieldName)
		# script = "SELECT {2} FROM {1} WHERE idGuild = '{0}'".format(ID, nameDB, fieldName)
		cursor.execute(script)
		value = cursor.fetchall()
	except:
		# Aucune données n'a été trouvé
		value = []

	# print("==== valueAt ====")
	# print(script)

	if value == []:
		return "Error 404"
	else:
		if fieldName == "all":
			return value
		else:
			return value[0]

#-------------------------------------------------------------------------------
def valueAtNumber(ID, fieldName, nameDB = None):
	if fieldName != "all":
		VAN = valueAt(ID, fieldName, nameDB)
		if VAN != 0 and VAN != None:
			VAN = VAN[0]
		return VAN
	else:
		return 0

## import library
from DataAccessLayer import DataAccessLayer
import os
import pandas as pd

class DataSetUpPackage():
    """
    Assuming you have your CSV and neo4j DB all setup.
    """
    def __init__(self, filePath=None, filename=None):
        self.Filename = filename or 'FishDB.csv'                # if you are using your own csv dataset
        self.FilePath = filePath or self.GetDefaultCSVPath      # if you directly clone from git hub < this will use ./RawCSV folder
        self.SessionInstance = None
        self.Disease_DF = None
        self.Verbose = False
        self.Disease_DF_RowIndex = 0
        
    @property
    def ReadCSVAndPopulateDB(self, indexCol=None):
        IndexCol = indexCol or 'ID'       
        self.Disease_DF = pd.read_csv(self.FilePath + self.Filename, encoding = "ISO-8859-1", index_col=IndexCol)
        return self
    
    @property    
    def GetDefaultCSVPath(self):
        folderpath = os.getcwd()
        if os.name == 'posix':
            folderpath += "/RawCSV/"
        else:
            folderpath +=  "\\RawCSV\\"
        return folderpath
    
    def CreateDiseaseNode(self, diseaseName=None):
        i = self.Disease_DF_RowIndex
        DiseaseName = diseaseName or self.Disease_DF.iloc[i,0] 
        query = (
            "MERGE (node: "+"Disease"+" {name: $name})"
            "RETURN node"
        )
        with self.SessionInstance as session:
            result = session.run(query, name=DiseaseName)
        if self.Verbose:
            print("create {0} node with name as {1}".format("Disease", DiseaseName))
            
    def SetDiseaseProps(self,diseaseName=None, environment=None,affected_fish=None,cause=None,treatment=None,vetadvice=None): 
        i = self.Disease_DF_RowIndex
        DiseaseName = diseaseName or self.Disease_DF.iloc[i,0] 
        Environment = environment or self.Disease_DF.iloc[i,2]
        Affected_fish = affected_fish or self.Disease_DF.iloc[i,3]
        Cause = cause or self.Disease_DF.iloc[i,16]
        Treatment = treatment or self.Disease_DF.iloc[i,17]
        Vet_advised = vetadvice or self.Disease_DF.iloc[i,18]
        query = (
            "MATCH (node: "+"Disease"+" {name: $name})"
            "SET node.environment = "+ "$env" + ", node.affectfish = "+ "$afish, node.cause = "+ "$cause, node.treatment = "+ "$treatment, node.vet_advised = "+ "$vetadvise "
            "RETURN node"
        )

        with self.SessionInstance as session:
            result = session.run(query, name=DiseaseName, 
                                 env=Environment, afish=Affected_fish,
                                 cause=Cause, treatment=Treatment, vetadvise=Vet_advised
                                )
        if self.Verbose:
            print("Set props on {0}-{1}:".format("Disease", DiseaseName))
            print("environment - {0}".format(Environment))
            print("affectfish - {0}".format(Affected_fish))
            print("cause - {0}".format(Cause))
            print("treatment - {0}".format(Treatment))
            print("vet_advised - {0}".format(Vet_advised))
    
    def CreateAKANode(self,diseaseName=None,aka=None):
        i = self.Disease_DF_RowIndex
        DiseaseName = diseaseName or self.Disease_DF.iloc[i,0] 
        AKA = aka or self.Disease_DF.iloc[i,1]
        if pd.isnull(AKA) == False:
            query = (
                        "MERGE (node: "+"AKA"+" {name: $name})"
                        "RETURN node"
                    )

            with self.SessionInstance as session:
                result = session.run(query, name=AKA)
            if self.Verbose:
                print("create {0} node with name as {1}".format("AKA", AKA))

            # add AKA relationship
            query = (
                "MATCH (n1 {name: $name1})"
                "MATCH (n2 {name: $name2})"
                "MERGE (n1) - [r:"+"AKA"+"] -> (n2)"   
                "RETURN n1, n2, r"
            )

            with self.SessionInstance as session:
                result = session.run(query, name1=DiseaseName, name2=AKA)
            if self.Verbose:
                print("create {0} -AKA-> {1}".format(DiseaseName, AKA))
                
    def CreateSymptomNode(self,diseaseName=None,symptomColIndexStart=None,symptomColIndexEnd=None):
        i = self.Disease_DF_RowIndex
        DiseaseName = diseaseName or self.Disease_DF.iloc[i,0]
        ColStart = symptomColIndexStart or 4
        ColEnd = symptomColIndexEnd or 15
        disease_df = self.Disease_DF
        for j in range(ColStart, ColEnd):
            # iterate across the associated symptoms  
            if pd.isnull(disease_df.iloc[i,j]) == False:
                # add symptom node
                query = (
                    "MERGE (node: "+"Symptom"+" {name: $name})"
                    "RETURN node"
                )
                with self.SessionInstance as session:
                    result = session.run(query, name=disease_df.iloc[i,j])
                if self.Verbose:
                    print("create {0} node with name as {1}".format("Symptom", disease_df.iloc[i,j]))

                # add Disease hasSymptom Symptom relationship
                query = (
                    "MATCH (n1 {name: $name1})"
                    "MATCH (n2 {name: $name2})"
                    "MERGE (n1) - [r:"+"hasSymptom"+"] -> (n2)"   
                    "RETURN n1, n2, r"
                )
                                
                with self.SessionInstance as session:
                    result = session.run(query, name1=DiseaseName, name2=disease_df.iloc[i,j])
                if self.Verbose:
                    print("create {0} -hasSymptom-> {1}".format(DiseaseName, disease_df.iloc[i,j]))
                    
                # add Symptom isDetectedIn Disease relationship
                query = (
                    "MATCH (n1 {name: $name1})"
                    "MATCH (n2 {name: $name2})"
                    "MERGE (n1) - [r:"+"isDetectedIn"+"] -> (n2)"   
                    "RETURN n1, n2, r"
                )

                with self.SessionInstance as session:
                    result = session.run(query, name1=disease_df.iloc[i,j], name2=DiseaseName)
                if self.Verbose:
                    print("create {0} -isDetectedIn-> {1}".format(disease_df.iloc[i,j], DiseaseName))
                    
            else:
                break
    
    def CreateMedicationNode (self,diseaseName=None,medColIndexStart=None,medColIndexEnd=None):
        i = self.Disease_DF_RowIndex
        DiseaseName = diseaseName or self.Disease_DF.iloc[i,0]
        ColStart = medColIndexStart or 19
        ColEnd = medColIndexEnd or 26
        disease_df = self.Disease_DF
        for j in range(ColStart, ColEnd):
            # iterate across the associated symptoms  
            if pd.isnull(disease_df.iloc[i,j]) == False:
                # add Medication node
                query = (
                    "MERGE (node: "+"Medication"+" {name: $name})"
                    "RETURN node"
                )
                with self.SessionInstance as session:
                    result = session.run(query, name=disease_df.iloc[i,j])
                if self.Verbose:
                    print("create {0} node with name as {1}".format("Medication", disease_df.iloc[i,j]))

                # add Disease useMedication Medication relationship
                query = (
                    "MATCH (n1 {name: $name1})"
                    "MATCH (n2 {name: $name2})"
                    "MERGE (n1) - [r:"+"useMedication"+"] -> (n2)"   
                    "RETURN n1, n2, r"
                )

                with self.SessionInstance as session:
                    result = session.run(query, name1=DiseaseName, name2=disease_df.iloc[i,j])
                if self.Verbose:
                    print("create {0} -useMedication-> {1}".format(DiseaseName, disease_df.iloc[i,j]))
                
                # add Medication knownTreatment Disease relationship
                query = (
                    "MATCH (n1 {name: $name1})"
                    "MATCH (n2 {name: $name2})"
                    "MERGE (n1) - [r:"+"knownTreatment"+"] -> (n2)"   
                    "RETURN n1, n2, r"
                )

                with self.SessionInstance as session:
                    result = session.run(query, name1=disease_df.iloc[i,j], name2=DiseaseName)
                if self.Verbose:
                    print("create {0} -knownTreatment-> {1}".format(disease_df.iloc[i,j], DiseaseName))
            else:
                break
    
    def PopulateNeo4j(self, neo4jSessionInstance, verbose=False):
        self.SessionInstance = neo4jSessionInstance
        self.Verbose = verbose
        disease_df = self.Disease_DF
        
        for i in range(disease_df.shape[0]):            
            # traverse row-by-row
            # set row index
            self.Disease_DF_RowIndex = i
            
            # Create disease nodes          
            self.CreateDiseaseNode()

            # Set some props to Disease
            # straight forward labelling are environment and affected fish at the moment
            # By right we should add Causes & Also treatment as Nodes
            # However, these are merely a chunk of text suitable only for props at this moment
            self.SetDiseaseProps()
            
            # Create AKA NODES - also known as
            self.CreateAKANode()
            
            # add symptom nodes and relationship to disease
            self.CreateSymptomNode()
            
            # add Med nodes
            self.CreateMedicationNode()
            
# To set up the neo4jDB
# Call the data access layer to first establish the data connection, then run the follow by uncommenting:
# dbcon = DataAccessLayer(username='neo4j',password='neo123456').CreateDBConnection
# dbcon.ClearCurrentDB  # This will clean up the neo4jDB
# DataSetUpPackage().ReadCSVAndPopulateDB.PopulateNeo4j(dbcon.Session, verbose=True)


# Once neo4jDB is setup
# at this moment you can
# 1) get all nodes of a type - eg  run the follow by uncommenting:

# dbcon = DataAccessLayer(username='neo4j',password='neo123456').CreateDBConnection
# result2 = dbcon.GetAllNodeListOfType('Disease')
# for resulti in result2:
#     print(resulti.name)
#     print(resulti.environment)
#     for r in resulti.symptoms:
#         print(r.name)


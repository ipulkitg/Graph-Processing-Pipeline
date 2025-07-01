import pyarrow.parquet as pq
import pandas as pd
from neo4j import GraphDatabase
import time


class DataLoader:

    def __init__(self, uri, user, password):
        """
        Connect to the Neo4j database and other init steps
        
        Args:
            uri (str): URI of the Neo4j database
            user (str): Username of the Neo4j database
            password (str): Password of the Neo4j database
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self.driver.verify_connectivity()


    def close(self):
        """
        Close the connection to the Neo4j database
        """
        self.driver.close()


    # Define a function to create nodes and relationships in the graph
    def load_transform_file(self, file_path):
        """
        Load the parquet file and transform it into a csv file
        Then load the csv file into neo4j
        Args:
        file_path (str): Path to the parquet file to be loaded
        """
        print(f"Starting data loading process for file: {file_path}")
        
        try:
            # Read the parquet file
            print("Reading parquet file...")
            trips = pq.read_table(file_path)
            trips = trips.to_pandas()
            print(f"Successfully read parquet file. Shape: {trips.shape}")
            
            # Some data cleaning and filtering
            print("Filtering data...")
            trips = trips[['tpep_pickup_datetime', 'tpep_dropoff_datetime', 'PULocationID', 'DOLocationID', 'trip_distance', 'fare_amount']]
            # Filter out trips that are not in bronx
            bronx = [3, 18, 20, 31, 32, 46, 47, 51, 58, 59, 60, 69, 78, 81, 94, 119, 126, 136, 147, 159, 167, 168, 169, 174, 182, 183, 184, 185, 199, 200, 208, 212, 213, 220, 235, 240, 241, 242, 247, 248, 250, 254, 259]
            trips = trips[trips.iloc[:, 2].isin(bronx) & trips.iloc[:, 3].isin(bronx)]
            trips = trips[trips['trip_distance'] > 0.1]
            trips = trips[trips['fare_amount'] > 2.5]
            print(f"After filtering, shape: {trips.shape}")
            
            # Convert date-time columns to the ISO format that Neo4j can parse
            trips['tpep_pickup_datetime'] = pd.to_datetime(trips['tpep_pickup_datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')
            trips['tpep_dropoff_datetime'] = pd.to_datetime(trips['tpep_dropoff_datetime']).dt.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Convert to csv and store in the current directory
            save_loc = "/var/lib/neo4j/import/" + file_path.split("/")[-1].split(".")[0] + '.csv'
            print(f"Saving CSV to: {save_loc}")
            trips.to_csv(save_loc, index=False)
            print("CSV saved successfully")
            
            # Load data into Neo4j
            print("Starting Neo4j data loading...")
            with self.driver.session() as session:
                # Create constraint for location nodes to ensure uniqueness
                print("Creating constraint...")
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE")
                
                # Create location nodes for pickup locations
                print("Creating pickup location nodes...")
                csv_filename = file_path.split("/")[-1].split(".")[0] + '.csv'
                print(f"CSV filename: {csv_filename}")
                
                session.run("""
                    LOAD CSV WITH HEADERS FROM 'file:///' + $file_name AS row
                    WITH DISTINCT toInteger(row.PULocationID) AS id
                    MERGE (l:Location {name: id})
                """, file_name=csv_filename)
                
                # Create location nodes for dropoff locations
                print("Creating dropoff location nodes...")
                session.run("""
                    LOAD CSV WITH HEADERS FROM 'file:///' + $file_name AS row
                    WITH DISTINCT toInteger(row.DOLocationID) AS id
                    MERGE (l:Location {name: id})
                """, file_name=csv_filename)
                
                # Create TRIP relationships between locations with modified datetime parsing
                print("Creating TRIP relationships...")
                session.run("""
                    LOAD CSV WITH HEADERS FROM 'file:///' + $file_name AS row
                    MATCH (pickup:Location {name: toInteger(row.PULocationID)})
                    MATCH (dropoff:Location {name: toInteger(row.DOLocationID)})
                    MERGE (pickup)-[trip:TRIP {
                        distance: toFloat(row.trip_distance),
                        fare: toFloat(row.fare_amount),
                        pickup_dt: datetime(row.tpep_pickup_datetime),
                        dropoff_dt: datetime(row.tpep_dropoff_datetime)
                    }]->(dropoff)
                """, file_name=csv_filename)
                
                # Check if data was loaded
                print("Checking data loading...")
                result = session.run("MATCH (n:Location) RETURN count(n) AS count")
                count = result.single()["count"]
                print(f"Number of Location nodes: {count}")
                
                result = session.run("MATCH ()-[r:TRIP]->() RETURN count(r) AS count")
                count = result.single()["count"]
                print(f"Number of TRIP relationships: {count}")
                
                print("Data loading completed")
                
        except Exception as e:
            print(f"Error during data loading: {e}")
            raise e
        
def main():
    total_attempts = 10
    attempt = 0
    # The database takes some time to startup!
    # Try to connect to the database 10 times
    while attempt < total_attempts:
        try:
            data_loader = DataLoader("neo4j://localhost:7687", "neo4j", "project1phase1")
            # Use the full path to the file
            data_loader.load_transform_file("/var/lib/neo4j/import/yellow_tripdata_2022-03.parquet")
            data_loader.close()
            attempt = total_attempts
        except Exception as e:
            print(f"(Attempt {attempt+1}/{total_attempts}) Error: ", e)
            attempt += 1
            time.sleep(10)


if __name__ == "__main__":
    main()
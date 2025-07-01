# Graph Processing Pipeline

Scalable graph processing system with Neo4j and distributed data pipeline using Kubernetes, Kafka, and Docker for NYC taxi trip analysis.

## Overview
Two-phase project implementing graph algorithms and building a highly scalable, real-time data processing pipeline that ingests document streams and performs graph analytics on distributed Neo4j clusters.

## Phase 1: Docker & Neo4j Foundation
- **Neo4j Setup**: Containerized graph database with NYC taxi trip data
- **Graph Algorithms**: PageRank and Breadth-First Search implementations
- **Data Loading**: Automated CSV ingestion with custom schema design
- **Docker Integration**: Complete containerization with plugin management

### Key Features
- Location nodes with trip relationships
- GDS plugin integration for advanced algorithms
- Automated data loading pipeline
- Remote access configuration

## Phase 2: Kubernetes Data Pipeline
- **Orchestration**: Minikube-based Kubernetes deployment
- **Stream Processing**: Kafka for real-time data ingestion
- **Distributed Storage**: Scalable Neo4j cluster setup
- **Connector Integration**: Kafka-Neo4j data bridge

### Architecture Components
- **Kafka**: Message streaming and data distribution
- **Zookeeper**: Kafka cluster coordination
- **Neo4j**: Graph database with GDS capabilities
- **Kafka Connect**: Real-time data pipeline to Neo4j

## Implementation

### Phase 1 Files
- `Dockerfile` - Neo4j container with data loading
- `data_loader.py` - NYC taxi data ingestion script
- `interface.py` - Graph algorithm implementations

### Phase 2 Files
- `zookeeper-setup.yaml` - Zookeeper deployment configuration
- `kafka-setup.yaml` - Kafka cluster setup
- `neo4j-values.yaml` - Neo4j Helm chart values
- `kafka-neo4j-connector.yaml` - Data pipeline connector
- `interface.py` - Updated algorithms for distributed environment

## Algorithms Implemented
1. **PageRank**: Location importance ranking based on taxi trip patterns
2. **Breadth-First Search**: Optimal path finding between locations

## Usage

### Phase 1: Standalone Neo4j
```bash
# Build and run container
docker build -t graph-processing .
docker run -p 7474:7474 -p 7687:7687 graph-processing

# Access Neo4j browser
http://localhost:7474
```

### Phase 2: Kubernetes Pipeline
```bash
# Start minikube cluster
minikube start --memory=4096 --cpus=4

# Deploy services
kubectl apply -f zookeeper-setup.yaml
kubectl apply -f kafka-setup.yaml
helm install neo4j neo4j/neo4j -f neo4j-values.yaml
kubectl apply -f kafka-neo4j-connector.yaml

# Expose services
minikube service kafka-service --url
minikube service neo4j-service --url
```

## Dataset
- **Source**: NYC Yellow Cab Trip Data (March 2022)
- **Schema**: Location nodes connected by trip relationships
- **Properties**: Distance, fare, pickup/dropoff timestamps
- **Scale**: Processing millions of taxi trips

## Requirements
- Docker & Docker Compose
- Kubernetes (Minikube)
- Helm package manager
- Neo4j GDS Plugin v2.3.1
- Kafka & Zookeeper

**Tech Stack**: Neo4j, Docker, Kubernetes, Kafka, Python, Graph Algorithms, Helm
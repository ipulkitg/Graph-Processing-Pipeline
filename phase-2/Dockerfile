# Base image: ubuntu:22.04
FROM ubuntu:22.04
# ARGs
ARG TARGETPLATFORM=linux/amd64,linux/arm64
ARG DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg software-properties-common curl apt-transport-https ca-certificates && \
    add-apt-repository universe

# Install Neo4j using their official instructions for Ubuntu
RUN curl -fsSL https://debian.neo4j.com/neotechnology.gpg.key | gpg --dearmor -o /usr/share/keyrings/neo4j.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/neo4j.gpg] https://debian.neo4j.com stable latest" | tee /etc/apt/sources.list.d/neo4j.list && \
    apt-get update && \
    apt-get install -y neo4j python3-pip nano unzip && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Download and install the Neo4j GDS plugin
RUN mkdir -p /var/lib/neo4j/plugins && \
    cd /var/lib/neo4j/plugins && \
    wget -O neo4j-graph-data-science-2.16.0.jar https://github.com/neo4j/graph-data-science/releases/download/2.16.0/neo4j-graph-data-science-2.16.0.jar && \
    chown -R neo4j:neo4j /var/lib/neo4j/plugins

# Configure Neo4j to allow GDS procedures
RUN echo 'dbms.security.procedures.unrestricted=gds.*' >> /etc/neo4j/neo4j.conf && \
    echo 'dbms.security.procedures.allowlist=gds.*' >> /etc/neo4j/neo4j.conf

# Install required Python packages
RUN pip3 install --upgrade pip pandas pyarrow neo4j requests 

# Create directory for project files
RUN mkdir -p /cse511

# Download the dataset
RUN mkdir -p /var/lib/neo4j/import && \
    cd /var/lib/neo4j/import && \
    wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet

# Configure Neo4j for remote access and set password
RUN sed -i 's/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/g' /etc/neo4j/neo4j.conf && \
    sed -i 's/#server.bolt.listen_address=:7687/server.bolt.listen_address=:7687/g' /etc/neo4j/neo4j.conf && \
    sed -i 's/#server.http.listen_address=:7474/server.http.listen_address=:7474/g' /etc/neo4j/neo4j.conf && \
    echo 'dbms.security.auth_enabled=true' >> /etc/neo4j/neo4j.conf && \
    neo4j-admin dbms set-initial-password project1phase1

# Copy Python scripts to the container
COPY data_loader.py interface.py tester.py /cse511/

# Run the data loader script
RUN chmod +x /cse511/data_loader.py 
RUN neo4j start
RUN cd /cse511
RUN cp /var/lib/neo4j/import/yellow_tripdata_2022-03.parquet /cse511/
RUN python3 /cse511/data_loader.py
RUN neo4j stop

# Expose neo4j ports
EXPOSE 7474 7687

# Start neo4j service and show the logs on container run
CMD ["/bin/bash", "-c", "neo4j start && tail -f /dev/null"]
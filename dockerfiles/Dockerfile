# Use the official ZooKeeper image from Docker Hub
FROM zookeeper:3.7

# Expose the port ZooKeeper runs on
EXPOSE 2181

# Set environment variables for ZooKeeper
ENV ZOO_MY_ID=1
ENV ZOO_SERVERS=server.1=0.0.0.0:2888:3888;2181
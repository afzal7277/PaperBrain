import os

PROJECT_NAME = "Smart-Warehouse-Management-System"

structure = {
    "data/raw": [
        "inventory.csv",
        "orders.csv",
        "stock_movement.csv",
        "suppliers.csv"
    ],
    "data/processed": [
        "daily_inventory_summary.csv",
        "sales_summary.csv",
        "alerts_generated.csv"
    ],
    "data/historical": [
        "sales_2024.csv",
        "sales_2025.csv"
    ],
    "data/historical/warehouse_logs": [],

    "kafka/producers": [
        "order_producer.py",
        "inventory_producer.py",
        "stock_movement_producer.py"
    ],
    "kafka/consumers": [
        "spark_kafka_consumer.py"
    ],
    "kafka/topics": [
        "topics.txt"
    ],

    "spark/streaming": [
        "kafka_to_cassandra.py",
        "stock_alerts_stream.py",
        "inventory_update_stream.py"
    ],
    "spark/batch": [
        "sales_analysis.py",
        "demand_forecasting.py",
        "inventory_optimization.py"
    ],
    "spark/utils": [
        "spark_session.py"
    ],

    "cassandra/schema": [
        "inventory_table.cql",
        "alerts_table.cql",
        "stock_movement_table.cql"
    ],
    "cassandra/data_loader": [
        "cassandra_insert.py"
    ],

    "hdfs/input/historical_data": [],
    "hdfs/output/reports": [],
    "hdfs/output/analytics_results": [],
    "hdfs/logs": [],

    "dashboard/backend": [
        "app.py",
        "database_connector.py"
    ],
    "dashboard/frontend": [
        "index.html",
        "styles.css",
        "scripts.js"
    ],
    "dashboard/assets": [],

    "alerts": [
        "alert_rules.py",
        "alert_logs.csv"
    ],

    "config": [
        "kafka_config.yaml",
        "spark_config.yaml",
        "cassandra_config.yaml",
        "hdfs_config.yaml"
    ],

    "docs/ppt_diagrams": [],
    "docs": [
        "architecture_diagram.png",
        "dataset_description.pdf",
        "system_workflow.pdf"
    ],

    "scripts": [
        "data_generator.py",
        "start_kafka.sh",
        "start_spark.sh",
        "start_cassandra.sh"
    ],

    "tests": [
        "test_kafka.py",
        "test_spark.py",
        "test_cassandra.py"
    ]
}

def create_structure():
    print(f"Creating project: {PROJECT_NAME}")
    os.makedirs(PROJECT_NAME, exist_ok=True)

    for folder, files in structure.items():
        folder_path = os.path.join(PROJECT_NAME, folder)
        os.makedirs(folder_path, exist_ok=True)

        for file in files:
            file_path = os.path.join(folder_path, file)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    pass

    # Root files
    root_files = [
        "README.md",
        "requirements.txt",
        ".gitignore"
    ]

    for file in root_files:
        with open(os.path.join(PROJECT_NAME, file), "w") as f:
            pass

    print("✅ Project structure created successfully!")

if __name__ == "__main__":
    create_structure()

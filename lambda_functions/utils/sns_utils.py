import boto3

def get_sns_client():
    return boto3.client("sns")

def get_or_create_sns_topic(zip_code):
    """Find existing SNS topic for zip code or create a new one."""
    sns = get_sns_client()
    topic_name = f"wildfire-alerts-{zip_code}"

    try:
        paginator = sns.get_paginator("list_topics")
        for page in paginator.paginate():
            for topic in page.get("Topics", []):
                if topic_name in topic["TopicArn"]:
                    print(f"Found existing SNS topic: {topic['TopicArn']}")
                    return topic["TopicArn"]

        response = sns.create_topic(Name=topic_name)
        print(f"Created new SNS topic: {response['TopicArn']}")
        return response["TopicArn"]

    except Exception as e:
        print(f"Failed to get or create SNS topic: {str(e)}")
        raise

def subscribe_user_to_topic(email, topic_arn):
    """Subscribe user's email to the SNS topic."""
    sns = get_sns_client()

    try:
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email
        )
        print(f"Subscribed {email} to SNS topic")
        return response
    except Exception as e:
        print(f"Failed to subscribe user: {str(e)}")
        raise

def send_clustered_alert(fires, email, topic_arn):
    """Send alert message summarizing grouped wildfires."""
    if fires.empty:
        return

    clusters = {}
    GRID_SIZE = 0.0725

    for _, fire in fires.iterrows():
        lat, lon = fire["latitude"], fire["longitude"]
        grid_lat = round(lat / GRID_SIZE) * GRID_SIZE
        grid_lon = round(lon / GRID_SIZE) * GRID_SIZE
        key = f"{grid_lat},{grid_lon}"

        if key not in clusters:
            clusters[key] = {"center": (grid_lat, grid_lon), "fires": []}
        clusters[key]["fires"].append(fire)

    alert_messages = []
    for cluster in clusters.values():
        fire = cluster["fires"][0]
        alert = (
            f"🔥 Wildfire Alert!\n"
            f"Location: {cluster['center'][0]:.4f}, {cluster['center'][1]:.4f}\n"
            f"Fires in cluster: {len(cluster['fires'])}\n"
            f"FRP: {fire['frp']} MW\n"
            f"Date: {fire['acq_date']}"
        )
        alert_messages.append(alert)

    final_message = "\n\n".join(alert_messages)

    sns = get_sns_client()
    try:
        sns.publish(TopicArn=topic_arn, Message=final_message, Subject="🔥 Wildfire Alert")
        print(f"Sent alert to {email} with {len(clusters)} clusters.")
    except Exception as e:
        print(f"Failed to send alert: {str(e)}")
        raise

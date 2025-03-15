import boto3

sns = boto3.client('sns')

def get_or_create_sns_topic(zip_code):
    """Find existing SNS topic for zip code or create a new one."""

    topic_name = f"wildfire-alerts-{zip_code}"
    
    # Check if SNS topic already exists
    topics = sns.list_topics().get('Topics', [])
    for topic in topics:
        if topic_name in topic['TopicArn']:
            print(f"Found existing SNS topic for zip code {zip_code}")
            return topic['TopicArn']
    
    # Create a new SNS topic if not found
    try:
        response = sns.create_topic(Name=topic_name)
        print(f"Created new SNS topic for zip code {zip_code}")
        return response['TopicArn']
    except Exception as e:
        print(f"Failed to create SNS topic: {str(e)}")
        raise

def subscribe_user_to_topic(email, topic_arn):
    """Subscribe user's email to the SNS topic."""

    try:
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        print(f"Subscribed {email} to SNS topic")
        return response
    except Exception as e:
        print(f"Failed to subscribe user: {str(e)}")
        raise

def send_clustered_alert(fires, email, topic_arn):
    """Group nearby fires and send a consolidated alert per cluster."""

    if fires.empty:
        return  # No fires to report

    clusters = {}
    GRID_SIZE = 0.0725  # ~5 miles in degrees

    # Group fires into 5-mile clusters
    for _, fire in fires.iterrows():
        lat, lon = fire['latitude'], fire['longitude']
        grid_lat, grid_lon = round(lat / GRID_SIZE) * GRID_SIZE, round(lon / GRID_SIZE) * GRID_SIZE
        grid_key = f"{grid_lat},{grid_lon}"

        if grid_key not in clusters:
            clusters[grid_key] = {'center': (grid_lat, grid_lon), 'fires': []}
        clusters[grid_key]['fires'].append(fire)

    # Format message for each cluster
    alert_messages = []
    for cluster in clusters.values():
        if not cluster['fires']:
            continue

        fire = cluster['fires'][0]  # Use first fire in cluster as representative
        message = (
            f"🔥 Wildfire Alert!\n"
            f"Location: {cluster['center'][0]:.4f}, {cluster['center'][1]:.4f}\n"
            f"Number of fires in cluster: {len(cluster['fires'])}\n"
            f"Fire Radiative Power: {fire['frp']} MW\n"
            f"Date: {fire['acq_date']}"
        )
        alert_messages.append(message)

    # Combine all cluster messages into a single alert
    final_alert = "\n\n".join(alert_messages)

    try:
        sns.publish(TopicArn=topic_arn, Message=final_alert, Subject="🔥 Wildfire Alert")
        print(f"Sent alert to {email} with {len(clusters)} clusters.")
    except Exception as e:
        print(f"Failed to send alert to {email}: {str(e)}")

import wandb

def AAA_site_classification():

    wandb.init(
        project="AAA",
        entity="your_entity_name",  # Replace with your WandB entity name
        name="AAA_site_classification",
        config={
            "learning_rate": 0.001,
            "epochs": 10,
            "batch_size": 32,
            "dataset": "AAA_dataset",
            "model": "ResNet50"
        }
    )

    # TODO to implement
    wandb.log({"o3-mini-accuracy": accuracy, "o3-f1": f1_score, "o3-precision": precision, "o3-recall": recall})

    wandb.finish()

def double_fencing_detection():
    
    wandb.init()
    # TODO

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run reasoning experiments')
    parser.add_argument('--experiment', choices=['site_classification', 'double_fencing'], required=True, help='Experiment to run')
    args = parser.parse_args()

    if args.experiment == 'site_classification':
        AAA_site_classification()
    elif args.experiment == 'double_fencing':
        double_fencing_detection()
    else:
        print("Please specify experiment type.")
        exit(1)
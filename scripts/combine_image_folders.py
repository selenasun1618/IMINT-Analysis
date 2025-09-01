import os
import shutil
from pathlib import Path

def combine_folders(base_dir, positive_folder, negative_folder, output_folder):
    """Combine images from positive and negative folders into a single output folder"""
    base_path = Path(base_dir)
    pos_path = base_path / positive_folder
    neg_path = base_path / negative_folder
    out_path = base_path / output_folder
    
    # Create output directory if it doesn't exist
    out_path.mkdir(exist_ok=True)
    
    copied_count = 0
    
    # Copy positive images
    if pos_path.exists():
        for img_file in pos_path.glob("*.png"):
            dest_file = out_path / img_file.name
            if not dest_file.exists():
                shutil.copy2(img_file, dest_file)
                copied_count += 1
                print(f"Copied: {img_file.name}")
    
    # Copy negative images  
    if neg_path.exists():
        for img_file in neg_path.glob("*.png"):
            dest_file = out_path / img_file.name
            if not dest_file.exists():
                shutil.copy2(img_file, dest_file)
                copied_count += 1
                print(f"Copied: {img_file.name}")
    
    print(f"✅ Combined {copied_count} images into {output_folder}")
    return copied_count

def main():
    # Double-Fences combinations
    df_base = "/Users/selenasun/Projects/IMINT-Images/Double-Fences"
    
    print("🔄 Combining Double-Fences datasets...")
    
    # Train set
    # combine_folders(df_base, "yes_df_train", "no_df_train", "df_train_combined")
    
    # Validation set
    # combine_folders(df_base, "yes_df_val", "no_df_val", "df_val_combined")
    
    # # Test set
    combine_folders(df_base, "yes_df_test", "no_df_test", "df_test_combined")
    
    # print("\n🔄 Combining AAA datasets...")
    
    # AAA combinations
    # aaa_base = "/Users/selenasun/Projects/IMINT-Images/AAA"
    
    # # Train set
    # combine_folders(aaa_base, "yes_aaa_train", "no_aaa_train", "aaa_train_combined")
    
    # # Validation set (if exists)
    # combine_folders(aaa_base, "yes_aaa_val", "no_aaa_val", "aaa_val_combined")
    
    # # Test set
    # combine_folders(aaa_base, "yes_aaa_test", "no_aaa_test", "aaa_test_combined")
    
    # print("\n✅ All datasets combined successfully!")

if __name__ == "__main__":
    main()

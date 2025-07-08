import pandas as pd
import re
from typing import List, Tuple

def preprocess_text(text: str) -> List[str]:
    """Preprocess text by converting to lowercase, removing punctuation, and splitting into words."""
    if pd.isna(text) or text == "":
        return []
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', '', str(text).lower())
    # Split into words and filter empty strings
    return [word for word in text.split() if word]

def calculate_wer(reference: List[str], hypothesis: List[str]) -> Tuple[float, int, int, int, int]:
    """
    Calculate Word Error Rate using dynamic programming.
    Returns: (WER, substitutions, insertions, deletions, total_words)
    """
    ref_len = len(reference)
    hyp_len = len(hypothesis)
    
    # Create matrix for dynamic programming
    dp = [[0] * (hyp_len + 1) for _ in range(ref_len + 1)]
    
    # Initialize first row and column
    for i in range(ref_len + 1):
        dp[i][0] = i
    for j in range(hyp_len + 1):
        dp[0][j] = j
    
    # Fill the matrix
    for i in range(1, ref_len + 1):
        for j in range(1, hyp_len + 1):
            if reference[i-1] == hypothesis[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = min(
                    dp[i-1][j] + 1,      # deletion
                    dp[i][j-1] + 1,      # insertion
                    dp[i-1][j-1] + 1     # substitution
                )
    
    # Backtrack to count error types
    i, j = ref_len, hyp_len
    substitutions = insertions = deletions = 0
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and reference[i-1] == hypothesis[j-1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            substitutions += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            deletions += 1
            i -= 1
        else:
            insertions += 1
            j -= 1
    
    total_errors = substitutions + insertions + deletions
    wer = total_errors / ref_len if ref_len > 0 else 0.0
    
    return wer, substitutions, insertions, deletions, ref_len

def main():
    # Load CSV files
    try:
        transcripts_df = pd.read_csv('transcripts_vosk-model-small-de-0.15_noise_reduce.csv')
        annotations_df = pd.read_csv('annotation.csv')
    except FileNotFoundError as e:
        print(f"Error loading CSV files: {e}")
        return
    
    # Join dataframes on file_name
    merged_df = pd.merge(annotations_df, transcripts_df, on='file_name', suffixes=('_ref', '_hyp'))
    
    print(f"Total files matched: {len(merged_df)}")
    print(f"Files in annotation: {len(annotations_df)}")
    print(f"Files in transcripts: {len(transcripts_df)}")
    print("-" * 50)
    
    # Calculate WER for each file
    total_substitutions = total_insertions = total_deletions = total_words = 0
    wer_scores = []
    
    for _, row in merged_df.iterrows():
        ref_words = preprocess_text(row['transcript_ref'])
        hyp_words = preprocess_text(row['transcript_hyp'])
        
        wer, subs, ins, dels, ref_len = calculate_wer(ref_words, hyp_words)
        
        total_substitutions += subs
        total_insertions += ins
        total_deletions += dels
        total_words += ref_len
        wer_scores.append(wer)
        
        #print(f"File: {row['file_name']}")
        #print(f"  Reference: {' '.join(ref_words)}")
        #print(f"  Hypothesis: {' '.join(hyp_words)}")
        #print(f"  WER: {wer:.3f} (S:{subs}, I:{ins}, D:{dels}, N:{ref_len})")
        #print()
    
    # Calculate overall statistics
    overall_wer = (total_substitutions + total_insertions + total_deletions) / total_words if total_words > 0 else 0
    average_wer = sum(wer_scores) / len(wer_scores) if wer_scores else 0
    
    print("=" * 50)
    print("OVERALL RESULTS")
    print("=" * 50)
    print(f"Total reference words: {total_words}")
    print(f"Total substitutions: {total_substitutions}")
    print(f"Total insertions: {total_insertions}")
    print(f"Total deletions: {total_deletions}")
    print(f"Total errors: {total_substitutions + total_insertions + total_deletions}")
    print(f"Overall WER: {overall_wer:.3f} ({overall_wer*100:.1f}%)")
    print(f"Average WER: {average_wer:.3f} ({average_wer*100:.1f}%)")

if __name__ == "__main__":
    main()

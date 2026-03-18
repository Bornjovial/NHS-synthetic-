# Synthetic Data Limitations

Synthetic data is artificially generated data that replicates the statistical properties or qualities of real-world datasets.

Typically, it is generated using real data and adding noise. However, in this pipeline **no real data is used** at any point.

Synthetic data is incredibly useful; it offers advantages in privacy preservation, scalability, and cost reduction. However, there are various limitations that are important to understand, particularly for our use case of generating synthetic clinical notes:

## Limitations

### 1. Loss of Real-World Complexity

Real-world clinical data is complex. A patient journey through hospital can be influenced by endless factors - from conflicting observations to staff availability. Meanwhile, clinical documentation is shaped by the implicit knowledge of staff, institutional practices and context-dependent decision-making.

Whilst our pipeline can generate high quality synthetic journeys and notes, it will fail to capture this richness.

### 2. Underrepresentation of Edge Cases

Rare scenarios can include atypical admissions, conflicting diagnoses, or adverse events which are difficult to generate reliably.

Whilst our pipeline intends to be able to generate a variety of synthetic clinical journeys and notes, these may tend to reflect 'average' cases rather than the long tail of real-world complexity.

### 3. Bias Amplification

Synthetic clinical notes can inherit biases from both the underlying Large Language Model (LLM) and the prompting strategy. These biases can manifest in:

- Overemphasis on certain conditions or treatments
- Systematic omission of specific patient groups or outcomes
- Stylised or homogenised documentation patterns

### 4. Hallucinations

LLMs generating synthetic notes and journeys may introduce plausible but incorrect clinical information. These hallucinations can include:

- Fabricated symptoms or test results
- Inaccurate timelines
- Inconsistent patient states across notes

## Actions to Take

If you do plan on using this pipeline to generate synthetic data, please consider:

1. **Synthetic data cannot replace real-world data.**

- Consider where real-world data can help with development and evaluation, alongside synthetic data.

3. **Assess the quality of your synthetic data.**
   
 - Clinicans can judge the quality of your outputs.
 - Consider using LLM Judges to asses the quality of your outputs.
 - Measure for bias, you could follow the methodology [here](https://link.springer.com/article/10.1186/s12911-025-03118-0).

4. **Make sure your data is not confused for real data.**

 - Add flags to ensure people do not confuse it for real patient data.
  
5. Additionally, read our `adapting_the_pipeline.md` and `input_data.md` file

- This will help you use our pipeline in the most effective way. 
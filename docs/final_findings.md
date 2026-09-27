# Final Project Findings

## 1. Initial baseline

The project started with a lightweight multilingual customer-support intent classifier based on:

- TF-IDF text features
- Logistic Regression
- Ukrainian and English messages
- 9 intent classes
- scenario-aware train/test splitting

The first version demonstrated that a simple linear NLP baseline was sufficient to establish a reproducible benchmark, but model errors revealed important limitations in the dataset.

## 2. Error analysis

Out-of-fold error analysis showed systematic confusion between semantically close intents.

The most important error groups included:

- ACCESS_ACCOUNT vs TECHNICAL_ISSUE
- SCHEDULE_DEADLINE vs CHANGE_CANCEL
- OTHER vs CONTENT_USAGE_QUESTION
- TECHNICAL_ISSUE vs SCHEDULE_DEADLINE

This showed that aggregate accuracy alone was insufficient for understanding model quality.

Error analysis was therefore used as a data-development tool rather than only as a reporting step.

## 3. Targeted data augmentation

Targeted augmentation was created specifically around the error patterns identified during error analysis.

On the frozen development population:

- baseline Accuracy: 0.6481
- baseline Macro F1: 0.6355
- baseline errors: 38

After targeted augmentation:

- Accuracy: 0.8519
- Macro F1: 0.8498
- errors: 16

Improvement:

- Accuracy: +0.2037
- Macro F1: +0.2143
- errors: -22

The final test set was not used during this iteration.

This was one of the main findings of the project: improving the training data based on observed error patterns produced a much larger gain than simple hyperparameter tuning.

## 4. Model comparison

After improving the dataset, several classical text-classification configurations were compared using grouped cross-validation.

The evaluated approaches included:

- word TF-IDF + Logistic Regression
- word n-grams + Logistic Regression
- character TF-IDF + Logistic Regression
- word TF-IDF + LinearSVC
- character TF-IDF + LinearSVC
- combined word + character TF-IDF + LinearSVC

The best cross-validation result was obtained with:

- combined word + character TF-IDF
- LinearSVC

Cross-validation Macro F1:

- 0.8039 ± 0.0706

An important finding was that the preferred model changed after the dataset was improved.

This demonstrates that model selection should be repeated after significant data changes.

## 5. Frozen final-test evaluation

After model and data decisions were completed, the final model was trained on all development data and evaluated once on the frozen final-test set.

Final production results:

- Accuracy: 0.8889
- Macro F1: 0.8861
- Weighted F1: 0.8861
- Errors: 4
- Final-test records: 36

The frozen test set was isolated from error analysis, augmentation design and model selection to reduce test-set leakage and optimistic evaluation.

## 6. Production quality gate

The production model metrics are stored separately in:

`config/production_model.json`

Current production benchmark:

- production Macro F1: 0.8861
- production Accuracy: 0.8889
- production errors: 4

The CI/CD pipeline evaluates every newly trained candidate against the production Macro F1.

A candidate is rejected when:

`candidate_macro_f1 < production_macro_f1`

This prevents automatic deployment of a model that performs worse than the current production version.

## 7. Production feedback loop

The inference service logs:

- request ID
- timestamp
- message length
- word count
- predicted intent
- inference duration

The application also collects explicit user feedback:

- correct prediction
- incorrect prediction
- corrected intent

Corrections are aggregated by predicted and corrected intent.

This provides the production data required for the next ML improvement cycle.

The system does not automatically retrain from every user correction.

Instead, the intended improvement process is:

production traffic
→ feedback collection
→ error review
→ curated dataset update
→ dataset validation/versioning
→ retraining
→ evaluation
→ quality gate
→ deployment

This keeps human validation between production feedback and model training.

## 8. Monitoring

Prometheus collects operational metrics including:

- prediction count
- prediction distribution by intent
- inference latency
- inference errors
- user feedback
- prediction corrections

Grafana visualizes six main production panels:

1. Average inference latency
2. Predictions per minute
3. Predictions by intent
4. User Feedback
5. Inference Errors
6. Prediction Corrections

Monitoring was verified using real requests through the deployed chat UI.

## 9. CI/CD and deployment

The final pipeline implements:

training
→ dataset validation
→ MLflow experiment tracking
→ frozen-test evaluation
→ model quality gate
→ application build
→ smoke tests
→ GHCR image publishing
→ automatic deployment to Hetzner
→ production health check
→ production prediction smoke test

Docker images are tagged with the Git commit SHA.

The exact same SHA is propagated to production through `IMAGE_TAG`.

This provides traceability between:

Git commit
→ CI run
→ Docker image
→ deployed production version.

## 10. Main project conclusions

The main technical conclusions from the project are:

1. Data quality and decision-boundary examples had a larger effect than basic hyperparameter tuning.
2. Error analysis should drive dataset development.
3. Model comparison must be repeated after major dataset changes.
4. A frozen final-test set must not participate in iterative model development.
5. Offline metrics alone are insufficient; production feedback and operational monitoring are necessary.
6. User corrections are valuable training signals, but should be curated before entering the training dataset.
7. A quality gate prevents silent regression during automated retraining.
8. Reproducible ML delivery requires linking dataset version, model evaluation, Docker image and production deployment.

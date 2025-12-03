"""
Level 2 RUN: Fine-Tuning for Autonomous Tool Acquisition Decisions

This module contains components for generating training data and fine-tuning
a model to autonomously make tool acquisition decisions.

Components:
- TrainingDataGenerator: Generate synthetic training examples from seeds
- (Future) QualityValidator: Validate generated examples
- (Future) FineTuningPipeline: Manage fine-tuning jobs
- (Future) EvaluationFramework: Evaluate model performance
"""

from .training_data_generator import TrainingDataGenerator, GenerationConfig, TrainingExample

__all__ = [
    "TrainingDataGenerator",
    "GenerationConfig",
    "TrainingExample",
]

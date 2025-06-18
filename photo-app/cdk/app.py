#!/usr/bin/env python3
import os
from aws_cdk import App
from photo_app_stack import PhotoAppStack

app = App()
PhotoAppStack(app, "PhotoAppStack")
app.synth()
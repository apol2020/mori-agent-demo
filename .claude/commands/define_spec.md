---
allowed-tools: Edit(specs/**), Write(specs/**), Read(**)
argument-hint: [spec_file.md]
description: 仕様書を指定して要件定義を開始する。達成したい要件を可能な限り詳しく記載します。
---
ultrathink

# Instructions.
Read $ARGUMENTS and make it concrete.
$ARGUMENTS contains what the user wants to implement.
Be sure to speak in Japanese.

You need to clarify the following

- What parts you are modifying (creating new)
- How to modify (create new)
- What kind of processing you want to do
  - Do not provide specific code.
    - Explain everything in Japanese.
  - Describe the process in words.
  - It is OK to include the output format json, etc.
- Implementation procedure (Task) and how to check the operation at each step
  - Divide the process into multiple steps that can be checked, and describe how to check the operation of each step.
- Requirements to be met in the end

The output should be in the form of an addition to $ARGUMENTS.


Find out what you can from the source code and documentation,
Ask the user if there are any questions or unclear points regarding the requirements.

# Compliance
Source code may not be included in the specification.
Diagrams should be created using Mermaid.
Please make sure that the content is easy to read and clear to third parties.
Non-functional requirements are not required.

# Andrej Karpathy's AI Coding Principles

## Source
- Repository: https://github.com/forrestchang/andrej-karpathy-skills
- Based on Andrej Karpathy's video "Claude Code: What Works and What Doesn't"
- Date discovered: [autonomous exploration]

## About Andrej Karpathy
Leading AI researcher and engineer:
- Built ImageNet (dataset that powered deep learning revolution)
- Co-created AlexNet architecture
- Contributed to OpenAI's early days
- Led Tesla's Autopilot vision team
- Created nanoGPT and other influential open-source projects

## Core Principles

### 1. Context Window Management
- Keep the context window clean and focused
- Remove irrelevant files from context
- Use file references strategically
- Don't overload with unnecessary information

### 2. Architectural Decisions
- Make key architectural decisions upfront
- Define interfaces and data structures early
- Think about scalability before implementation
- Document assumptions explicitly

### 3. Test-Driven Development
- Write tests first whenever possible
- Use tests to define expected behavior
- Run tests frequently to catch issues early
- Tests serve as living documentation

### 4. Iterative Refinement
- Build incrementally, not all at once
- Get feedback loops tight
- Refactor as you go, don't wait
- Small steps, frequent validation

### 5. Error Handling
- Handle errors gracefully
- Provide meaningful error messages
- Log errors appropriately
- Fail fast when appropriate

### 6. Code Organization
- Keep functions small and focused
- Separate concerns clearly
- Use meaningful names
- Structure for maintainability

### 7. Documentation
- Document as you code
- Explain why, not just what
- Keep documentation in sync
- Good docs are self-documenting code

### 8. Verification
- Verify assumptions explicitly
- Check outputs match expectations
- Use assertions where appropriate
- Don't assume, verify

### 9. Communication
- Be explicit about what you want
- Provide clear examples
- Give context when needed
- Ask clarifying questions

### 10. Debugging
- Start simple, add complexity
- Use print statements strategically
- Isolate problems
- Think step-by-step

## Practical Workflows

### When Starting a New Feature
1. Define the interface/API first
2. Write tests for the expected behavior
3. Implement the core logic
4. Add error handling
5. Refactor and optimize

### When Debugging
1. Reproduce the issue consistently
2. Add logging/prints at key points
3. Isolate the minimal failing case
4. Fix and verify
5. Add a test to prevent regression

### When Refactoring
1. Ensure tests pass before starting
2. Make small, incremental changes
3. Run tests after each change
4. Review for clarity and simplicity
5. Commit frequently

## Why This Approach Works

1. **Sets Clear Expectations**: The AI knows exactly what principles to follow
2. **Provides Mental Models**: Gives the AI frameworks for thinking about problems
3. **Reduces Ambiguity**: Clear guidelines reduce guesswork
4. **Encourages Best Practices**: Promotes testing, documentation, and verification
5. **Is Concise**: Easy to reference, not overwhelming

## Key Takeaway
> "Think before you code, test before you implement, iterate quickly, document as you go, verify assumptions, keep it simple, fail fast, communicate clearly."

---
*Note: These principles are universally applicable to software development, not just AI-assisted coding.*

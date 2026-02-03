# AI Model Agnosticism Manifesto

## Philosophy

A well-designed AI model wrapper script should be **completely agnostic** to the models it processes. The script's role is orchestration, not gatekeeping. Model-specific knowledge belongs in configuration files (profiles), not in code.

## Core Principles

### 1. **Profiles Are the Source of Truth**

The profile defines everything about how to interact with a model:
- Which API endpoint to call
- What parameters the model accepts
- How to modify prompts (prefix/suffix)
- Pricing information for cost tracking
- Timing constraints (rate limiting, delays)

**The script must trust the profile completely.**

### 2. **No Hardcoded Model Logic**

The script should NEVER contain:
- Hardcoded lists of "supported models"
- Conditional logic based on endpoint names
- Parameter filtering based on model type
- Model-specific validation rules

If you find yourself writing `if model == "some-model-name"`, you're doing it wrong.

### 3. **Pass Everything Through**

All parameters defined in a profile's `parameters` section should be:
- Loaded from YAML exactly as written
- Passed to the API exactly as loaded
- Never filtered, modified, or validated by the script

The API itself will validate parameters and return errors if something is wrong.

### 4. **Let APIs Fail Gracefully**

If a profile specifies invalid parameters:
- The API will reject the request
- The script will log the error
- The user will fix the profile
- No code changes required

This is the correct failure mode.

## Why This Matters

### Flexibility
- Support ANY model without code changes
- Add new model types (image, video, audio) without refactoring
- Users can experiment with new APIs immediately

### Maintainability
- No need to update code when APIs add new parameters
- No need to track which models support which features
- Validation logic lives in one place (the API)

### Scalability
- Support 1 model or 1000 models with the same code
- Each profile is independent and self-contained
- New use cases don't require developer intervention

## Anti-Patterns to Avoid

### ❌ Endpoint Whitelisting
```python
supported_models = ['model-a', 'model-b']
if endpoint in supported_models:
    # validate parameters
```
**Why it's wrong**: Requires code changes for every new model.

### ❌ Parameter Filtering
```python
if 'image_urls' in params:
    if endpoint != 'model-that-needs-it':
        params.pop('image_urls')
```
**Why it's wrong**: Script shouldn't guess what parameters are valid.

### ❌ Model-Specific Validation
```python
if endpoint == 'model-a':
    if 'required_param' not in params:
        raise ValueError("Missing required_param")
```
**Why it's wrong**: API will reject invalid requests anyway.

### ❌ Type Coercion Based on Model
```python
if endpoint == 'model-a':
    params['value'] = [params['value']]  # convert to list
```
**Why it's wrong**: Profile should specify the correct format.

## Correct Patterns

### ✅ Generic Parameter Passing
```python
# Load profile
profile = yaml.safe_load(profile_file)

# Extract parameters
endpoint = profile['endpoint']
params = profile.get('parameters', {})

# Send to API (no filtering, no validation)
api_client.call(endpoint, params)
```

### ✅ Profile-Driven Configuration
```yaml
# Profile defines everything
endpoint: "fal-ai/any-model"
parameters:
  any_param: "any_value"
  even_new_params: "that_dont_exist_yet"
```

### ✅ API Error Handling
```python
try:
    result = api_client.call(endpoint, params)
except APIError as e:
    logger.error(f"API rejected request: {e}")
    # User fixes profile, no code changes needed
```

## Practical Examples

### Example 1: Aspect Ratio Control
```yaml
endpoint: "fal-ai/gemini-25-flash-image/edit"
parameters:
  image_urls: "https://example.com/aspect_ratio_9x16.png"
  num_images: 1
prompt_suffix: "Match the aspect ratio of the reference image"
```

### Example 2: Character Reference
```yaml
endpoint: "fal-ai/gemini-25-flash-image/edit"
parameters:
  image_urls:
    - "https://example.com/character1.jpg"
    - "https://example.com/character2.jpg"
  num_images: 1
prompt_suffix: "Use provided images as character references"
```

### Example 3: BYOK Image Editing
```yaml
endpoint: "fal-ai/gpt-image-1/edit-image/byok"
parameters:
  image_urls: "https://example.com/logo.png"
  openai_api_key: "${OPENAI_API_KEY}"
  quality: "high"
  background: "transparent"
prompt_prefix: "Bold colors, vector art style"
```

**All three should work identically from the script's perspective.**

## Implementation Checklist

When building or refactoring an AI model wrapper:

- [ ] Remove all hardcoded model/endpoint names from code
- [ ] Remove parameter filtering logic
- [ ] Remove model-specific validation rules
- [ ] Pass all profile parameters directly to API
- [ ] Let API validate and return errors
- [ ] Document profile schema, not supported models
- [ ] Test with multiple different model types
- [ ] Ensure adding a new model requires zero code changes

## The Test

**Can a user add support for a brand new model by only creating a profile YAML file?**

- If yes: Your script is model-agnostic ✅
- If no: You have hardcoded model logic ❌

## Conclusion

Model agnosticism is not just a nice-to-have—it's the correct architectural pattern for AI wrapper scripts. It separates concerns, reduces maintenance burden, and empowers users to adapt to the rapidly evolving AI landscape without waiting for code updates.

**The script orchestrates. The profile configures. The API validates.**

Keep these boundaries clear, and your wrapper will remain flexible for years to come.

---

*This manifesto is model-agnostic, language-agnostic, and framework-agnostic. Apply these principles to any AI integration project.*

from pydantic import BaseModel, validator, root_validator, Field


class TypeValue(BaseModel):
    Value: str | None


class ContextDataValues(BaseModel):
    skin_tone: TypeValue | None = Field(alias='skinTone')
    eye_color: TypeValue | None = Field(alias='eyeColor')
    skin_type: TypeValue | None = Field(alias='skinType')
    hair_color: TypeValue | None = Field(alias='hairColor')
    is_staff: TypeValue | None = Field(alias='StaffContext')
    incentivized_review: TypeValue | None = Field(alias='IncentivizedReview')

    @validator('is_staff', 'incentivized_review')
    def str_to_int(cls, field):
        """Transforms 'true'/'false' -> 1/0."""
        if field.Value.lower() == 'true':
            field.Value = 1
            return field.Value
        elif field.Value.lower() == 'false':
            field.Value = 0
            return field.Value

    @validator('skin_tone', 'eye_color', 'skin_type', 'hair_color')
    def get_value(cls, field):
        return field.Value


class Result(BaseModel):
    author_id: int | None = Field(alias='AuthorId')
    rating: int | None = Field(alias='Rating')
    is_recommended: int | None = Field(alias='IsRecommended')
    helpfulness: float | None = Field(alias='Helpfulness')
    total_feedback_count: int | None = Field(alias='TotalFeedbackCount')
    total_neg_feedback_count: int | None = Field(alias='TotalNegativeFeedbackCount')
    total_pos_feedback_count: int | None = Field(alias='TotalPositiveFeedbackCount')
    submission_time: str | None = Field(alias='SubmissionTime')
    review_text: str | None = Field(alias='ReviewText')
    review_title: str | None = Field(alias='Title')
    context_values: ContextDataValues = Field(alias='ContextDataValues', exclude=True)  # auxiliary field

    @validator('review_text', 'review_title')
    def clear_text(cls, field):
        """Clears the review text and title from extraneous characters."""
        if field is not None:
            field = field.replace("'", '’').replace("\n", '').replace('"', '“').replace(' ', '').replace(' ', '')
        return field

    @validator('submission_time')
    def truncate_time(cls, field):
        """Transforms '2022-06-23T14:04:17.000+00:00' -> '2022-06-23'."""
        return field[:10]

    @root_validator  # for context_values
    def get_nested_values(cls, values):
        """Extracts all dictionaries from context_values"""
        for k, v in values['context_values'].dict().items():
            if v is not None:
                if type(v) == str:
                    values[f'{k}'] = f'{v}'
                else:
                    values[f'{k}'] = int(v)
            else:
                values[f'{k}'] = None
        return values


class ReviewInfo(BaseModel):
    Results: list[Result]
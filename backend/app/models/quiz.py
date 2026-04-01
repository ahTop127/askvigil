from tortoise import fields, models

class QuizQuestion(models.Model):
    id = fields.IntField(pk=True)
    category = fields.ForeignKeyField('models.ScamCategory', related_name='questions', null=True, on_delete=fields.SET_NULL)
    scenario_text = fields.TextField()
    explanation = fields.TextField(null=True)

    class Meta:
        table = "quiz_questions"

class QuizOption(models.Model):
    id = fields.IntField(pk=True)
    question = fields.ForeignKeyField('models.QuizQuestion', related_name='options', on_delete=fields.CASCADE)
    option_text = fields.TextField()
    is_correct = fields.BooleanField(default=False)

    class Meta:
        table = "quiz_options"

class QuizAttempt(models.Model):
    id = fields.IntField(pk=True)
    session = fields.ForeignKeyField('models.UserSession', related_name='quiz_attempts', on_delete=fields.CASCADE)
    question = fields.ForeignKeyField('models.QuizQuestion', related_name='attempts', on_delete=fields.CASCADE)
    selected_option = fields.ForeignKeyField('models.QuizOption', related_name='selections', on_delete=fields.CASCADE)
    is_correct = fields.BooleanField()
    attempted_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "quiz_attempts"
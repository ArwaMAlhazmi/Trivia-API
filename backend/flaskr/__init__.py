import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
def paginate_questions(request, questions):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in questions]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)
  
  '''
  Set up CORS. Allow '*' for origins.
  '''
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

  '''
  Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


  '''
  An endpoint to handle GET requests
  for all available categories.
  '''
  @app.route('/categories')
  def retrieve_categories():
    categories = Category.query.order_by(Category.id).all()
    formatedCategories = {category.id: category.type for category in categories}

    if len(categories) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'categories': formatedCategories
    })


  '''
  An endpoint to handle GET requests for questions,
  including pagination (every 10 questions).
  This endpoint returns a list of questions,
  number of total questions, current category, categories.
  '''

  @app.route('/questions')
  def retrieve_questions():
    questions = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, questions)

    categories = Category.query.order_by(Category.id).all()
    formatedCategories = {category.id: category.type for category in categories}

    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(Question.query.all()),
      'categories': formatedCategories,
      'current_category': None
    })

  ''' 
  An endpoint to DELETE question using a question ID.
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):

    question = Question.query.filter(Question.id == question_id).one_or_none()
    if question is None:
      abort(404)

    try:
      question.delete()

      return jsonify({
        'success': True,
        'deleted': question_id
      })

    except:
      abort(422)

  ''' 
  An endpoint to POST a new question,
  which will require the question and answer text,
  category, and difficulty score.
  '''
  '''
  POST endpoint to get questions based on a search term.
  It returns all questions for whom the search term
  is a substring of the question.
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()
    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None)
    new_category = body.get('category', None)
    search = body.get('searchTerm', None)

    if search:
      questions = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search))).all()
      current_questions = paginate_questions(request, questions)

      if len(questions) == 0:
        abort(404)

      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(questions),
      })

    else:
      try:
        question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
        question.insert()

        return jsonify({
          'success': True
        })

      except:
        abort(422)

  '''
  GET endpoint to get questions based on category.
  '''
  @app.route('/categories/<category_id>/questions')
  def retrieve_catigoryQuestions(category_id):

    current_category = Category.query.filter(Category.id == category_id).one_or_none()

    if current_category == None:
      abort(404)

    questions = Question.query.filter(Question.category == category_id).all()
    categoryQuestions = paginate_questions(request, questions)

    if len(questions) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': categoryQuestions,
      'total_questions': len(questions),
      'current_category': current_category.format()
    })

  ''' 
  POST endpoint to get questions to play the quiz.
  This endpoint takes category and previous question parameters
  and return a random questions within the given category,
  if provided, and that is not one of the previous questions.
  '''
  @app.route('/quizzes', methods=['POST'])
  def retrieve_quizQuestion():
    body = request.get_json()
    previousQuestions = body.get('previous_questions', None)
    quizCategory = body.get('quiz_category', None)['id']

    #Check for category choice to get questions based on category
    if quizCategory:
      questions = Question.query.filter(Question.category == quizCategory).all()
    else:
      #No category secifirs get all quetions
      questions = Question.query.all()

    #Get questions IDs in an array to choose random ID from
    questionsIds = [question.format()['id'] for question in questions]

    #If questionsIds and used questions the same length, no question to be send, otherwise send a random question
    if len(questionsIds) == len(previousQuestions):
      newQuizQuestion = None
    else:
      #Get a random ID from questionsIds that has not been used before
      randomQuestionId = random.choice([i for i in questionsIds if i not in previousQuestions])
      #Append the ID to the used IDs
      previousQuestions.append(randomQuestionId)
      #Get the question by ID
      newQuizQuestion = Question.query.get(randomQuestionId).format()

    return jsonify({
      'success': True,
      'question': newQuizQuestion,
      'previous_questions': previousQuestions
    })

  '''
  Error handlers for expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "resource not found"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "bad request"
      }), 400

  return app
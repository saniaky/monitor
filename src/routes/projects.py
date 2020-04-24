from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.db import db
from database.incident import Incident, incident_schema
from database.incident_update import IncidentUpdate
from database.project import Project, project_schema
from database.user import User, short_user_schema
from database.user_project import UserProject, UserProjectRole

projects = Blueprint('projects', __name__)


@projects.route('/projects', methods=['GET'])
@jwt_required
def get_projects():
    user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=user_id).scalar()
    return jsonify(project_schema.dump(user.projects, many=True))


@projects.route('/projects', methods=['POST'])
@jwt_required
def create_project():
    user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=user_id).first_or_404()
    body = request.get_json()
    project = Project(**body)
    user_project = UserProject(user=user, project=project, role=UserProjectRole.ADMIN)
    project.user_project.append(user_project)
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict())


@projects.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required
def update_project(project_id):
    user_id = get_jwt_identity()
    body = request.get_json()
    project = Project.query.filter_by(project_id=project_id).first_or_404()
    user = User.query.filter_by(user_id=user_id).first_or_404()
    if user not in project.members:
        return jsonify({'error': 'You dont have rights.'}), 401
    Project.query.filter_by(project_id=project_id).update(body)
    db.session.commit()
    print(body)
    return jsonify({'result': True})


@projects.route('/projects/<int:entity_id>', methods=['GET'])
@jwt_required
def read(entity_id):
    # TODO query for user
    return jsonify({entity_id: 'entity_id'})


@projects.route('/projects/<int:entity_id>', methods=['PUT'])
@jwt_required
def update(entity_id):
    new_name = request.json['name']
    project = Project.query.get(entity_id)
    if not project:
        return {'error': 'Project not found'}, 400
    project.name = new_name
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict())


@projects.route('/projects/<int:entity_id>', methods=['DELETE'])
@jwt_required
def delete(entity_id):
    db.session.delete(Project.query.get(entity_id))
    db.session.commit()
    return jsonify({'result': True})


@projects.route('/projects/<int:project_id>/incidents', methods=['GET'])
@jwt_required
def get_incidents(project_id):
    user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=user_id).first_or_404()
    project = Project.query.filter_by(project_id=project_id).first_or_404()
    if user not in project.members:
        return jsonify({'error': 'You dont have rights.'}), 401
    return jsonify(incident_schema.dump(project.incidents, many=True))


@projects.route('/projects/<int:project_id>/incidents', methods=['POST'])
@jwt_required
def create_incident(project_id):
    user_id = get_jwt_identity()
    body = request.get_json()
    user = User.query.filter_by(user_id=user_id).first_or_404()
    project = Project.query.filter_by(project_id=project_id).first_or_404()
    if user not in project.members:
        return jsonify({'error': 'You dont have rights.'}), 401
    new_incident = Incident(
        name=body['name'],
        components=body['components'],
        project_id=project_id,
        author_id=user_id)
    incident_update = IncidentUpdate(
        status=body['status'],
        message=body['message']
    )
    new_incident.updates.append(incident_update)
    project.incidents.append(new_incident)
    db.session.add(project)
    db.session.commit()
    return jsonify(short_user_schema.dump(project.incidents, many=True))


@projects.route('/projects/<int:project_id>/components', methods=['GET'])
@jwt_required
def get_components(project_id):
    user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=user_id).first_or_404()
    project = Project.query.filter_by(project_id=project_id).first_or_404()
    if user not in project.members:
        return jsonify({'error': 'You dont have rights.'}), 401
    return jsonify(short_user_schema.dump(project.members, many=True))


@projects.route('/projects/<int:project_id>/subscribers', methods=['GET'])
@jwt_required
def get_subscribers(project_id):
    user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=user_id).first_or_404()
    project = Project.query.filter_by(project_id=project_id).first_or_404()
    if user not in project.members:
        return jsonify({'error': 'You dont have rights.'}), 401
    return jsonify(short_user_schema.dump(project.members, many=True))


@projects.route('/projects/<int:project_id>/members', methods=['GET'])
@jwt_required
def get_project_members(project_id):
    user_id = get_jwt_identity()
    user = User.query.filter_by(user_id=user_id).first_or_404()
    project = Project.query.filter_by(project_id=project_id).first_or_404()
    if user not in project.members:
        return jsonify({'error': 'You dont have rights.'}), 401
    return jsonify(short_user_schema.dump(project.members, many=True))


def is_id_exist(project_id):
    return db.session.query(Project.project_id).filter_by(project_id=project_id).scalar() is not None

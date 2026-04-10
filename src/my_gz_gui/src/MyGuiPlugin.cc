#include "my_gz_gui/MyGuiPlugin.hh"

#include <algorithm>
#include <array>
#include <cstdlib>
#include <filesystem>
#include <set>
#include <string>
#include <vector>

#include <QBuffer>
#include <QImage>
#include <QMetaObject>
#include <QStringList>

#include <geometry_msgs/msg/pose_stamped.hpp>
#include <gz/gui/Application.hh>
#include <gz/gui/MainWindow.hh>
#include <gz/math/Quaternion.hh>
#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/empty.pb.h>
#include <gz/msgs/entity.pb.h>
#include <gz/msgs/entity_factory.pb.h>
#include <gz/msgs/image.pb.h>
#include <gz/msgs/physics.pb.h>
#include <gz/msgs/pose.pb.h>
#include <gz/msgs/scene.pb.h>
#include <gz/plugin/Register.hh>
#include <gz/transport/Node.hh>
#include <rclcpp/rclcpp.hpp>

namespace my_gz_gui
{

struct MyGuiPlugin::Impl
{
  gz::transport::Node node;
  rclcpp::Node::SharedPtr rosNode;
  rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr goalPosePub;
  bool ownsRosContext{false};

  std::string topicCmdVel{"/msauber/cmd_vel"};
  std::string topicGoalPose{"/goal_pose"};
  std::string topicSpawn{"/world/default/create"};
  std::string topicRemove{"/world/default/remove"};
  std::string topicSetPose{"/world/default/set_pose"};
  std::string topicPhysics{"/world/default/set_physics"};
  std::string topicSceneInfo;  // derived from spawn topic if not set

  QStringList modelList;
  QStringList robotList;
  QStringList spawnableList;
  std::set<std::string> knownRobotNames{"msauber"};
  QString cameraImageSource;
  std::string currentCameraTopic;
  std::set<std::string> cameraSubscriptions;
};

namespace
{

std::vector<std::filesystem::path> ResourceRoots()
{
  std::vector<std::filesystem::path> roots;
  std::set<std::string> seen;

  const std::array<const char *, 2> envVars{
    "GZ_SIM_RESOURCE_PATH",
    "IGN_GAZEBO_RESOURCE_PATH",
  };

  for (const auto *envVar : envVars)
  {
    const char *value = std::getenv(envVar);
    if (!value)
      continue;

    std::string allPaths(value);
    std::size_t start = 0;
    while (start <= allPaths.size())
    {
      auto end = allPaths.find(':', start);
      auto token = allPaths.substr(start, end - start);
      if (!token.empty() && seen.insert(token).second)
        roots.emplace_back(token);

      if (end == std::string::npos)
        break;
      start = end + 1;
    }
  }

  return roots;
}

QStringList DiscoverSpawnables()
{
  std::set<std::string> resources;

  for (const auto &root : ResourceRoots())
  {
    if (!std::filesystem::exists(root) || !std::filesystem::is_directory(root))
      continue;

    for (const auto &entry : std::filesystem::directory_iterator(root))
    {
      if (!entry.is_directory())
        continue;

      const auto configPath = entry.path() / "model.config";
      const auto sdfPath = entry.path() / "model.sdf";
      if (!std::filesystem::exists(configPath) && !std::filesystem::exists(sdfPath))
        continue;

      resources.insert("model://" + entry.path().filename().string());
    }
  }

  QStringList list;
  for (const auto &resource : resources)
    list.append(QString::fromStdString(resource));

  return list;
}

QString DefaultNameFromUri(const QString &_uri)
{
  const auto trimmed = _uri.trimmed();
  if (trimmed.isEmpty())
    return {};

  auto normalized = trimmed;
  if (normalized.endsWith('/'))
    normalized.chop(1);

  const auto lastSlash = normalized.lastIndexOf('/');
  const auto lastColon = normalized.lastIndexOf(':');
  const auto splitIndex = std::max(lastSlash, lastColon);
  auto baseName = splitIndex >= 0 ? normalized.mid(splitIndex + 1) : normalized;
  baseName.replace('-', '_');
  return baseName;
}

QString CameraTopicForRobot(const QString &_robotName)
{
  const auto trimmed = _robotName.trimmed();
  if (trimmed.isEmpty())
    return {};

  return "/" + trimmed + "/front_camera/image";
}

QString ImageToDataUrl(const gz::msgs::Image &_msg)
{
  QImage image;

  switch (_msg.pixel_format_type())
  {
    case gz::msgs::RGB_INT8:
      image = QImage(
        reinterpret_cast<const uchar *>(_msg.data().data()),
        static_cast<int>(_msg.width()),
        static_cast<int>(_msg.height()),
        static_cast<int>(_msg.step()),
        QImage::Format_RGB888).copy();
      break;
    case gz::msgs::BGR_INT8:
      image = QImage(
        reinterpret_cast<const uchar *>(_msg.data().data()),
        static_cast<int>(_msg.width()),
        static_cast<int>(_msg.height()),
        static_cast<int>(_msg.step()),
        QImage::Format_BGR888).copy();
      break;
    case gz::msgs::RGBA_INT8:
      image = QImage(
        reinterpret_cast<const uchar *>(_msg.data().data()),
        static_cast<int>(_msg.width()),
        static_cast<int>(_msg.height()),
        static_cast<int>(_msg.step()),
        QImage::Format_RGBA8888).copy();
      break;
    default:
      return {};
  }

  if (image.isNull())
    return {};

  QByteArray bytes;
  QBuffer buffer(&bytes);
  buffer.open(QIODevice::WriteOnly);
  image.save(&buffer, "PNG");
  return "data:image/png;base64," + bytes.toBase64();
}

}  // namespace

MyGuiPlugin::MyGuiPlugin()
  : impl(std::make_unique<Impl>())
{
}

MyGuiPlugin::~MyGuiPlugin()
{
  this->impl->goalPosePub.reset();
  this->impl->rosNode.reset();

  if (this->impl->ownsRosContext &&
      rclcpp::contexts::get_global_default_context()->is_valid())
    rclcpp::shutdown();
}

void MyGuiPlugin::LoadConfig(const tinyxml2::XMLElement *_pluginElem)
{
  if (this->title.empty())
    this->title = "MSAUBER Control";

  if (!_pluginElem)
    return;

  auto elem = _pluginElem->FirstChildElement("topic_cmd_vel");
  if (elem && elem->GetText())
    this->impl->topicCmdVel = elem->GetText();

  elem = _pluginElem->FirstChildElement("topic_spawn");
  if (elem && elem->GetText())
    this->impl->topicSpawn = elem->GetText();

  elem = _pluginElem->FirstChildElement("topic_goal_pose");
  if (elem && elem->GetText())
    this->impl->topicGoalPose = elem->GetText();

  elem = _pluginElem->FirstChildElement("topic_remove");
  if (elem && elem->GetText())
    this->impl->topicRemove = elem->GetText();

  elem = _pluginElem->FirstChildElement("topic_set_pose");
  if (elem && elem->GetText())
    this->impl->topicSetPose = elem->GetText();

  elem = _pluginElem->FirstChildElement("topic_physics");
  if (elem && elem->GetText())
    this->impl->topicPhysics = elem->GetText();

  elem = _pluginElem->FirstChildElement("topic_scene_info");
  if (elem && elem->GetText())
    this->impl->topicSceneInfo = elem->GetText();

  elem = _pluginElem->FirstChildElement("title");
  if (elem && elem->GetText())
    this->title = elem->GetText();

  // Derive scene_info topic from spawn topic if not explicitly set
  // e.g. "/world/pista/create" -> "/world/pista/scene/info"
  if (this->impl->topicSceneInfo.empty())
  {
    auto &spawn = this->impl->topicSpawn;
    auto pos = spawn.rfind('/');
    if (pos != std::string::npos)
      this->impl->topicSceneInfo = spawn.substr(0, pos) + "/scene/info";
    else
      this->impl->topicSceneInfo = "/world/default/scene/info";
  }

  if (!rclcpp::contexts::get_global_default_context()->is_valid())
  {
    int argc = 0;
    char **argv = nullptr;
    rclcpp::init(argc, argv);
    this->impl->ownsRosContext = true;
  }

  this->impl->rosNode = std::make_shared<rclcpp::Node>("my_gz_gui_goal_panel");
  this->impl->goalPosePub =
    this->impl->rosNode->create_publisher<geometry_msgs::msg::PoseStamped>(
      this->impl->topicGoalPose, 10);
}

QString MyGuiPlugin::PluginTitle() const
{
  return QString::fromStdString(this->title);
}

QStringList MyGuiPlugin::ModelList() const
{
  return this->impl->modelList;
}

QStringList MyGuiPlugin::RobotList() const
{
  return this->impl->robotList;
}

QStringList MyGuiPlugin::SpawnableList() const
{
  return this->impl->spawnableList;
}

QString MyGuiPlugin::CameraImageSource() const
{
  return this->impl->cameraImageSource;
}

void MyGuiPlugin::RefreshModelList()
{
  const auto newSpawnableList = DiscoverSpawnables();
  if (newSpawnableList != this->impl->spawnableList)
  {
    this->impl->spawnableList = newSpawnableList;
    emit spawnableListChanged();
  }

  gz::msgs::Empty req;
  gz::msgs::Scene rep;
  bool result{false};

  if (!this->impl->node.Request(
        this->impl->topicSceneInfo, req, 2000u, rep, result) || !result)
  {
    qWarning() << "Scene info service call failed on topic:"
               << QString::fromStdString(this->impl->topicSceneInfo);
    return;
  }

  QStringList newList;
  QStringList newRobotList;
  for (int i = 0; i < rep.model_size(); ++i)
  {
    const auto modelName = QString::fromStdString(rep.model(i).name());
    newList.append(modelName);

    if (this->impl->knownRobotNames.count(rep.model(i).name()) > 0 &&
        !newRobotList.contains(modelName))
      newRobotList.append(modelName);
  }

  if (newList != this->impl->modelList)
  {
    this->impl->modelList = newList;
    emit modelListChanged();
  }

  if (newRobotList != this->impl->robotList)
  {
    this->impl->robotList = newRobotList;
    emit robotListChanged();
  }
}

void MyGuiPlugin::OnSelectRobot(const QString &robotName)
{
  const auto cameraTopic = CameraTopicForRobot(robotName);
  this->impl->currentCameraTopic = cameraTopic.toStdString();

  if (cameraTopic.isEmpty())
  {
    if (!this->impl->cameraImageSource.isEmpty())
    {
      this->impl->cameraImageSource.clear();
      emit cameraImageSourceChanged();
    }
    return;
  }

  const auto topicKey = cameraTopic.toStdString();
  if (this->impl->cameraSubscriptions.insert(topicKey).second)
  {
    std::function<void(const gz::msgs::Image &)> callback =
      [this, topicKey](const gz::msgs::Image &_msg)
      {
        if (this->impl->currentCameraTopic != topicKey)
          return;

        const auto imageUrl = ImageToDataUrl(_msg);
        if (imageUrl.isEmpty())
          return;

        QMetaObject::invokeMethod(
          this,
          [this, imageUrl]()
          {
            if (this->impl->cameraImageSource == imageUrl)
              return;

            this->impl->cameraImageSource = imageUrl;
            emit cameraImageSourceChanged();
          },
          Qt::QueuedConnection);
      };

    this->impl->node.Subscribe<gz::msgs::Image>(topicKey, callback);
  }
}

void MyGuiPlugin::OnSetPose(const QString &modelName,
                            double x, double y, double z, double yaw)
{
  gz::msgs::Pose req;
  req.set_name(modelName.toStdString());
  req.mutable_position()->set_x(x);
  req.mutable_position()->set_y(y);
  req.mutable_position()->set_z(z);

  auto q = gz::math::Quaterniond(0, 0, yaw);
  req.mutable_orientation()->set_x(q.X());
  req.mutable_orientation()->set_y(q.Y());
  req.mutable_orientation()->set_z(q.Z());
  req.mutable_orientation()->set_w(q.W());

  gz::msgs::Boolean rep;
  bool result{false};
  if (!this->impl->node.Request(
        this->impl->topicSetPose, req, 2000u, rep, result) || !result)
  {
    qWarning() << "SetPose service call failed for model:" << modelName;
  }
}

void MyGuiPlugin::OnSpawnModel(const QString &modelUri,
                               const QString &modelName,
                               double x, double y, double z,
                               double roll, double pitch, double yaw)
{
  const auto trimmedUri = modelUri.trimmed();
  if (trimmedUri.isEmpty())
  {
    qWarning() << "Spawn skipped because no model URI was selected";
    return;
  }

  auto resolvedName = modelName.trimmed();
  if (resolvedName.isEmpty())
    resolvedName = DefaultNameFromUri(trimmedUri);

  if (resolvedName.isEmpty())
  {
    qWarning() << "Spawn skipped because model name is empty";
    return;
  }

  if (this->impl->modelList.contains(resolvedName))
  {
    qWarning() << "Spawn skipped because model name already exists:" << resolvedName;
    return;
  }

  gz::msgs::EntityFactory req;
  req.set_sdf_filename(trimmedUri.toStdString());
  req.set_name(resolvedName.toStdString());
  req.mutable_pose()->mutable_position()->set_x(x);
  req.mutable_pose()->mutable_position()->set_y(y);
  req.mutable_pose()->mutable_position()->set_z(z);
  auto q = gz::math::Quaterniond(roll, pitch, yaw);
  req.mutable_pose()->mutable_orientation()->set_x(q.X());
  req.mutable_pose()->mutable_orientation()->set_y(q.Y());
  req.mutable_pose()->mutable_orientation()->set_z(q.Z());
  req.mutable_pose()->mutable_orientation()->set_w(q.W());

  gz::msgs::Boolean rep;
  bool result{false};
  if (!this->impl->node.Request(
        this->impl->topicSpawn, req, 2000u, rep, result) || !result)
  {
    qWarning() << "Spawn service call failed for model:" << resolvedName;
    return;
  }

  this->RefreshModelList();
}

void MyGuiPlugin::OnRemoveModel(const QString &modelName)
{
  const auto trimmedName = modelName.trimmed();
  if (trimmedName.isEmpty())
  {
    qWarning() << "Remove skipped because no entity was selected";
    return;
  }

  gz::msgs::Entity req;
  req.set_name(trimmedName.toStdString());
  req.set_type(gz::msgs::Entity::MODEL);

  gz::msgs::Boolean rep;
  bool result{false};
  if (!this->impl->node.Request(
        this->impl->topicRemove, req, 2000u, rep, result) || !result)
  {
    qWarning() << "Remove service call failed for model:" << trimmedName;
    return;
  }

  this->RefreshModelList();
}

void MyGuiPlugin::OnSetGravity(double gz)
{
  gz::msgs::Physics req;
  req.mutable_gravity()->set_z(gz);

  gz::msgs::Boolean rep;
  bool result{false};
  if (!this->impl->node.Request(
        this->impl->topicPhysics, req, 2000u, rep, result) || !result)
  {
    qWarning() << "SetGravity service call failed";
  }
}

void MyGuiPlugin::OnSendGoalPose(double x, double y, double z,
                                 double roll, double pitch, double yaw)
{
  if (!this->impl->goalPosePub || !this->impl->rosNode)
  {
    qWarning() << "Goal pose publisher is not ready";
    return;
  }

  geometry_msgs::msg::PoseStamped msg;
  msg.header.frame_id = "map";
  msg.header.stamp = this->impl->rosNode->now();
  msg.pose.position.x = x;
  msg.pose.position.y = y;
  msg.pose.position.z = z;

  const auto q = gz::math::Quaterniond(roll, pitch, yaw);
  msg.pose.orientation.x = q.X();
  msg.pose.orientation.y = q.Y();
  msg.pose.orientation.z = q.Z();
  msg.pose.orientation.w = q.W();

  this->impl->goalPosePub->publish(msg);
}

}  // namespace my_gz_gui

GZ_ADD_PLUGIN(
  my_gz_gui::MyGuiPlugin,
  gz::gui::Plugin
)

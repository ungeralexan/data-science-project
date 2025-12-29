// src/components/pages/Register.tsx
import { useState } from "react";
import {
  Form,
  Input,
  Button,
  Typography,
  Card,
  message,
  Space,
  Select,
  Divider,
} from "antd";
import { MailOutlined, LockOutlined, UserOutlined } from "@ant-design/icons";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { POSSIBLE_LANGUAGE_OPTIONS, POSSIBLE_INTEREST_KEYWORDS } from "../../config";
import "../css/AuthPages.css";

/*
  Register page component that provides a form for users to create a new account.

  Includes:
  - First name, last name, email, password, confirm password
  - Mandatory interest keywords + optional free-text interests
  - Submit button triggers registration
  - Link to Login
*/

const { Title, Text } = Typography;

interface RegisterFormValues {
  email: string;
  password: string;
  confirmPassword: string;
  first_name: string;
  last_name: string;
  interest_keys: string[];
  interest_text?: string;
  language_preference?: string;
}

export default function Register() {
  // Loading state during registration
  const [loading, setLoading] = useState(false);

  // Button label to reflect what's happening (nice UX for long operations)
  const [submitButtonText, setSubmitButtonText] = useState("Sign Up");

  const { register } = useAuth();
  const navigate = useNavigate();
  const [messageApi, contextHolder] = message.useMessage();

  const onFinish = async (values: RegisterFormValues) => {
    setLoading(true);

    try {
      messageApi.success(
        "We are now generating your event recommendations. This might take a moment ..."
      );
      setSubmitButtonText("Creating your account ...");

      await register({
        email: values.email,
        password: values.password,
        first_name: values.first_name,
        last_name: values.last_name,
        interest_keys: values.interest_keys,
        interest_text: values.interest_text || "",
        language_preference: values.language_preference || "English",
      });

      messageApi.success("Welcome aboard! You are now being redirected ...");
      navigate("/events");
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : "Registration failed");
    } finally {
      setLoading(false);
      setSubmitButtonText("Sign Up");
    }
  };

  return (
    <div className="auth-container">
      {contextHolder}

      <Card className="auth-card">
        <Space direction="vertical" size="large" className="auth-space-full-width">
          <div className="auth-text-center">
            <Title level={2} className="auth-title">
              Create Account
            </Title>
            <Text type="secondary">Sign up for a new account</Text>
          </div>

          {/* Wrap to control desktop width (if you styled .auth-form-wrap) */}
          <div className="auth-form-wrap">
            <Form name="register" onFinish={onFinish} layout="vertical" size="large">
              <Form.Item
                name="first_name"
                rules={[{ required: true, message: "Please enter your first name" }]}
              >
                <Input prefix={<UserOutlined />} placeholder="First Name" />
              </Form.Item>

              <Form.Item
                name="last_name"
                rules={[{ required: true, message: "Please enter your last name" }]}
              >
                <Input prefix={<UserOutlined />} placeholder="Last Name" />
              </Form.Item>

              <Form.Item
                name="email"
                rules={[
                  { required: true, message: "Please enter your email" },
                  { type: "email", message: "Please enter a valid email" },
                ]}
              >
                <Input prefix={<MailOutlined />} placeholder="Email" />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[
                  { required: true, message: "Please enter your password" },
                  { min: 6, message: "Password must be at least 6 characters" },
                ]}
              >
                <Input.Password prefix={<LockOutlined />} placeholder="Password" />
              </Form.Item>

              <Form.Item
                name="confirmPassword"
                dependencies={["password"]}
                rules={[
                  { required: true, message: "Please confirm your password" },

                  // Validator to check if passwords match
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue("password") === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error("Passwords do not match"));
                    },
                  }),
                ]}
              >
                <Input.Password prefix={<LockOutlined />} placeholder="Confirm Password" />
              </Form.Item>

              <Divider>Your Interests and Preferred Event Language</Divider>

              <Text type="secondary" className="auth-interests-hint">
                Select your interests and preferred event language to receive personalized event recommendations. You can change
                these later in Settings.
              </Text>

              <Form.Item
                name="interest_keys"
                label="Interest Keywords"
                rules={[
                  { required: true, message: "Please select at least one interest" },
                  { type: "array", min: 1, message: "Please select at least one interest" },
                ]}
              >
                <Select
                  mode="multiple"
                  placeholder="Select your interests"
                  options={POSSIBLE_INTEREST_KEYWORDS.map((keyword) => ({
                    label: keyword,
                    value: keyword,
                  }))}
                  allowClear
                />
              </Form.Item>

              <Form.Item name="interest_text" label="Additional Interests (Optional)">
                <Input.TextArea
                  rows={3}
                  placeholder="Describe any additional interests not covered above..."
                />
              </Form.Item>

              <Form.Item
                name="language_preference"
                label="Preferred Event Language"
                rules={[
                  { required: true, message: "Please select your preferred event language" },
                ]}
              >
                <Select
                  placeholder="Select your preferred event language"
                  options={POSSIBLE_LANGUAGE_OPTIONS.map((language) => ({
                    label: language,
                    value: language,
                  }))}
                  allowClear
                />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  {submitButtonText}
                </Button>
              </Form.Item>
            </Form>
          </div>

          <div className="auth-text-center">
            <Text type="secondary">
              Already have an account? <Link to="/login">Sign in</Link>
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
}

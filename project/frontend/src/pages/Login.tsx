// src/pages/Login.tsx
import { useState } from 'react';
import { Form, Input, Button, Typography, Card, message, Space } from 'antd';
import { MailOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import '../components/css/AuthPages.css';

/*
    Login page component that provides a form for users to sign in.

    The page includes:
    - A title and subtitle welcoming users back.
    - A form with fields for email and password, including validation rules.
    - A submit button that triggers the login process.
    - Links for "Forgot your password?" and "Sign up" for new users.

    The component uses Ant Design components for styling and layout,
    and it interacts with the authentication context to perform the login operation.
*/

const { Title, Text } = Typography;

// Interface for form values
interface LoginFormValues {
    email: string;
    password: string;
}

export default function Login() {

    // State to manage loading state during login process
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    // messageApi is provided by Ant Design for displaying messages to users
    const [messageApi, contextHolder] = message.useMessage();

    // Function to handle form submission
    const onFinish = async (values: LoginFormValues) => {

        // Set loading state to true while processing login
        setLoading(true);

        try {

            // Perform login using the authentication context with provided email and password
            await login({
                email: values.email,
                password: values.password,
            });

            // On successful login, show success message and navigate to home page
            messageApi.success('Login successful!');
            navigate('/');

        } catch (error) {
            messageApi.error(error instanceof Error ? error.message : 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    //Render the login form and related UI elements
    return (
        <div className="auth-container">

            {/* 
                Ant Design message context holder 

                This is where messages will be shown
            */}
            {contextHolder}

            <Card className="auth-card">
                <Space direction="vertical" size="large" className="auth-space-full-width">
                    <div className="auth-text-center">
                        <Title level={2} className="auth-title">Welcome to Tuevent</Title>
                        <Text type="secondary">Sign in to your account</Text>
                    </div>

                    {/* Login form */}
                    <Form
                        name="login"
                        onFinish={onFinish} // onFinish is called when the form is submitted
                        layout="vertical"
                        size="large"
                    >
                        <Form.Item
                            name="email"
                            rules={[
                                { required: true, message: 'Please enter your email' },
                                { type: 'email', message: 'Please enter a valid email' },
                            ]}
                        >
                            <Input
                                prefix={<MailOutlined />}
                                placeholder="Email"
                            />
                        </Form.Item>

                        <Form.Item
                            name="password"
                            rules={[
                                { required: true, message: 'Please enter your password' },
                            ]}
                        >
                            <Input.Password
                                prefix={<LockOutlined />}
                                placeholder="Password"
                            />
                        </Form.Item>

                        <Form.Item>
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={loading}
                                block // Makes the button take the full width of its container
                            >
                                Sign In
                            </Button>
                        </Form.Item>

                        {/* Forgot password link */}
                        <Form.Item className="auth-form-item-no-margin">
                            <Link to="/forgot-password">
                                <Button type="link" className="auth-link-button">
                                    Forgot your password?
                                </Button>
                            </Link>
                        </Form.Item>
                    </Form>

                    <div className="auth-text-center">
                        <Text type="secondary">
                            Don't have an account?{' '}
                            <Link to="/register">Sign up</Link>
                        </Text>
                    </div>
                </Space>
            </Card>
        </div>
    );
}

// src/pages/ResetPassword.tsx
import { useState } from 'react';
import { Form, Input, Button, Typography, Card, message, Space, Alert } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import '../components/css/AuthPages.css';
import { API_BASE_URL } from '../config';

/*
    Reset Password page component that allows users to set a new password using a reset token.

    The page includes:
    - A title and subtitle guiding users to enter a new password.
    - A form with fields for the new password and confirmation, including validation rules.
    - A submit button that triggers the password reset process.
    - An alert for invalid or expired reset links.

*/

const { Title, Text } = Typography;

// Interface for form values
interface ResetPasswordFormValues {
    password: string;
    confirmPassword: string;
}

// ResetPassword component
export default function ResetPassword() {
    
    // State to manage loading state and success state
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    // Get token from URL query parameters
    const [searchParams] = useSearchParams();

    // Message API for displaying messages
    const navigate = useNavigate();
    const [messageApi, contextHolder] = message.useMessage();

    // Extract token from query parameters
    // Example: http://example.com/reset-password?token=abc123 -> token = "abc123"
    const token = searchParams.get('token');

    // Function to handle form submission (onFinish is called when form is submitted)
    const onFinish = async (values: ResetPasswordFormValues) => {
        if (!token) {
            messageApi.error('Invalid reset link');
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/reset-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },

                // Send token and new password in the request body
                // The token will be used by the backend to verify the reset request
                body: JSON.stringify({
                    token: token,
                    new_password: values.password,
                }),
            });

            // Parse the JSON response from the backend which is expected to contain a detail message
            // indicating success or failure of the password reset operation
            const data = await response.json();

            if (response.ok) {
                setSuccess(true);
                messageApi.success('Password reset successfully!');
                // Redirect to login after 2 seconds

                setTimeout(() => {
                    navigate('/login');
                }, 2000);
                
            } else {
                messageApi.error(data.detail || 'Failed to reset password');
            }
        } catch {
            messageApi.error('Failed to reset password');
        } finally {
            setLoading(false);
        }
    };

    // No token provided
    if (!token) {
        return (
            <div className="auth-container">
                <Card className="auth-card">
                    <Space direction="vertical" size="large" className="auth-space-full-width">
                        <Alert
                            message="Invalid Reset Link"
                            description="This password reset link is invalid or has expired. Please request a new one."
                            type="error"
                            showIcon
                        />
                        <div className="auth-text-center">
                            <Link to="/forgot-password">
                                <Button type="primary">Request New Reset Link</Button>
                            </Link>
                        </div>
                    </Space>
                </Card>
            </div>
        );
    }

    return (
        <div className="auth-container">
            {contextHolder}
            <Card className="auth-card">
                <Space direction="vertical" size="large" className="auth-space-full-width">
                    <div className="auth-text-center">
                        <Title level={2} className="auth-title">Reset Password</Title>
                        <Text type="secondary">
                            Enter your new password below.
                        </Text>
                    </div>

                    {success ? (
                        <Space direction="vertical" size="middle" className="auth-space-full-width">
                            <Alert
                                message="Password Reset Successful"
                                description="Your password has been reset. Redirecting to login..."
                                type="success"
                                showIcon
                            />
                        </Space>
                    ) : (
                        <>
                            <Form
                                name="reset-password"
                                onFinish={onFinish}
                                layout="vertical"
                                size="large"
                            >
                                <Form.Item
                                    name="password"
                                    rules={[
                                        { required: true, message: 'Please enter your new password' },
                                        { min: 6, message: 'Password must be at least 6 characters' },
                                    ]}
                                >
                                    <Input.Password
                                        prefix={<LockOutlined />}
                                        placeholder="New Password"
                                    />
                                </Form.Item>

                                <Form.Item
                                    name="confirmPassword"
                                    dependencies={['password']}
                                    rules={[
                                        { required: true, message: 'Please confirm your new password' },
                                        ({ getFieldValue }) => ({
                                            validator(_, value) {
                                                if (!value || getFieldValue('password') === value) {
                                                    return Promise.resolve();
                                                }
                                                return Promise.reject(new Error('Passwords do not match'));
                                            },
                                        }),
                                    ]}
                                >
                                    <Input.Password
                                        prefix={<LockOutlined />}
                                        placeholder="Confirm New Password"
                                    />
                                </Form.Item>

                                <Form.Item>
                                    <Button
                                        type="primary"
                                        htmlType="submit"
                                        loading={loading}
                                        block
                                    >
                                        Reset Password
                                    </Button>
                                </Form.Item>
                            </Form>

                            <div className="auth-text-center">
                                <Text type="secondary">
                                    Remember your password?{' '}
                                    <Link to="/login">Sign in</Link>
                                </Text>
                            </div>
                        </>
                    )}
                </Space>
            </Card>
        </div>
    );
}
